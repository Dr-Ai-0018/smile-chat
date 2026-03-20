"""
SessionStateService - 维护短期状态
计算 preset（动态状态参数）供每轮对话使用
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from storage import JsonStorage

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)


@dataclass
class SessionPreset:
    """动态状态参数（传给LLM的preset）"""
    recent_self_disclosure_rate: float  # 最近5轮中自我表露比例
    recent_self_disclosure_count_in_last_5: int  # 最近5轮中自我表露次数
    recent_self_disclosure_window_size: int  # 最近统计窗口大小（<=5）
    relationship_stage_judge: str  # 上一轮关系阶段 A/B/C（供下一轮参考）
    last_relationship_stage: str  # 兼容字段：同 relationship_stage_judge
    conversation_duration_min: int  # 本轮对话持续分钟数
    conversation_duration_human: str  # 本轮对话持续时长（自然表达）
    local_time_bucket: str  # morning/afternoon/evening/late_night
    turn_count: int  # 本会话轮次
    time_since_last_chat: int = 0  # 距上次完整会话结束的分钟数
    time_since_last_chat_human: str = "0分钟"  # 距上次完整会话结束时长（自然表达）
    timezone: str = "UTC+8"  # 统一时区标识
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class SessionStateService:
    """会话状态服务"""
    
    def __init__(self, storage: Optional[JsonStorage] = None):
        self.storage = storage or JsonStorage()
        self._session_cache: Dict[int, Dict[str, Any]] = {}
    
    def get_or_create_session(self, user_id: int) -> Dict[str, Any]:
        """获取或创建用户会话状态"""
        if user_id in self._session_cache:
            return self._session_cache[user_id]
        
        # 初始化新会话 - 使用中国时间
        session = {
            "user_id": user_id,
            "start_time": get_china_now().isoformat(),
            "turn_count": 0,
            "last_relationship_stage": "A",
            "self_disclosure_condition": "emotional",  # 默认情感表露组
        }
        self._session_cache[user_id] = session
        return session
    
    def compute_preset(self, user_id: int) -> SessionPreset:
        """
        计算本轮的动态状态参数

        Returns:
            SessionPreset 对象，用于注入到LLM context
        """
        session = self.get_or_create_session(user_id)

        # 1. 计算最近5轮自我表露统计（从聊天历史读取）
        disclosure_count, disclosure_window_size, disclosure_rate = self._compute_disclosure_stats(user_id)

        # 2. 获取 last_relationship_stage（从聊天历史最近一条 assistant 消息读取）
        last_stage = self._get_last_relationship_stage(user_id) or session.get("last_relationship_stage", "A")

        # 3~5. 优先从持久化实验状态读取
        try:
            exp_state = self.storage.get_user_experiment_state(user_id)
        except Exception:
            exp_state = {}

        # conversation_duration_min：当前会话开始到现在
        session_start_str = exp_state.get("session_start_time") or session.get("start_time")
        if session_start_str:
            try:
                start_time = datetime.fromisoformat(session_start_str)
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=CHINA_TZ)
                duration = (get_china_now() - start_time).total_seconds() / 60
                duration_min = max(0, int(duration))
            except Exception:
                duration_min = 0
        else:
            duration_min = 0
        duration_human = self._humanize_minutes(duration_min)

        # local_time_bucket
        time_bucket = self._get_time_bucket()

        # turn_count：从持久化状态读取
        turn_count = exp_state.get("current_round_count", session.get("turn_count", 0))

        # time_since_last_chat：距上次完整聊天结束时间
        last_end_str = exp_state.get("last_session_end_time")
        if last_end_str:
            try:
                last_end_time = datetime.fromisoformat(last_end_str)
                if last_end_time.tzinfo is None:
                    last_end_time = last_end_time.replace(tzinfo=CHINA_TZ)
                time_since = max(0, int((get_china_now() - last_end_time).total_seconds() / 60))
            except Exception:
                time_since = 0
        else:
            time_since = 0
        time_since_human = self._humanize_minutes(time_since)

        return SessionPreset(
            recent_self_disclosure_rate=disclosure_rate,
            recent_self_disclosure_count_in_last_5=disclosure_count,
            recent_self_disclosure_window_size=disclosure_window_size,
            relationship_stage_judge=last_stage,
            last_relationship_stage=last_stage,
            conversation_duration_min=duration_min,
            conversation_duration_human=duration_human,
            local_time_bucket=time_bucket,
            turn_count=turn_count,
            time_since_last_chat=time_since,
            time_since_last_chat_human=time_since_human,
        )
    
    def _get_last_relationship_stage(self, user_id: int) -> Optional[str]:
        """从最近一条 assistant 消息的 meta 读取关系阶段"""
        history = self.storage.get_chat_history(user_id=user_id, limit=20)
        for m in reversed(history):
            if m.get("role") == "assistant":
                stage = m.get("meta", {}).get("relationship_stage") or m.get("meta", {}).get("relationship_stage_judge")
                if stage in ("A", "B", "C"):
                    return stage
        return None

    def _compute_disclosure_stats(self, user_id: int) -> tuple[int, int, float]:
        """计算最近5轮对话的自我表露统计（次数/窗口/比例）"""
        history = self.storage.get_chat_history(user_id=user_id, limit=40)

        # 按轮次分组：每遇到 user 消息开启新轮，收集该轮所有 assistant 消息
        rounds: List[List[dict]] = []
        current_round_assistants: List[dict] = []
        for m in history:
            if m.get("role") == "user":
                if current_round_assistants:
                    rounds.append(current_round_assistants)
                current_round_assistants = []
            elif m.get("role") == "assistant":
                current_round_assistants.append(m)
        if current_round_assistants:
            rounds.append(current_round_assistants)

        # 取最近5轮，每轮用最后一条 assistant 消息
        recent_5 = [r[-1] for r in rounds[-5:]]
        if not recent_5:
            return 0, 0, 0.0

        disclosure_count = sum(
            1 for m in recent_5
            if m.get("meta", {}).get("did_self_disclosure", False)
            or m.get("meta", {}).get("self_disclosure_triggered", False)
        )
        window_size = len(recent_5)
        return disclosure_count, window_size, disclosure_count / window_size

    def _humanize_minutes(self, minutes: int) -> str:
        minutes = max(0, int(minutes))
        if minutes <= 0:
            return "0分钟"
        if minutes < 60:
            return f"{minutes}分钟"
        if minutes < 1440:
            hours, remain = divmod(minutes, 60)
            if remain == 0:
                return f"{hours}小时"
            return f"{hours}小时{remain}分钟"
        days, remain_minutes = divmod(minutes, 1440)
        hours, remain = divmod(remain_minutes, 60)
        if hours == 0 and remain == 0:
            return f"{days}天"
        if remain == 0:
            return f"{days}天{hours}小时"
        return f"{days}天{hours}小时{remain}分钟"
    
    def _get_time_bucket(self) -> str:
        """获取当前时间段 - 使用中国时间"""
        hour = get_china_now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 23:
            return "evening"
        else:
            return "late_night"
    
    def update_after_response(
        self,
        user_id: int,
        relationship_stage: str,
        did_self_disclosure: bool
    ):
        """
        响应后更新状态
        
        Args:
            user_id: 用户ID
            relationship_stage: 本轮模型判断的关系阶段
            did_self_disclosure: 本轮是否触发了自我表露
        """
        session = self.get_or_create_session(user_id)
        
        # 更新关系阶段
        if relationship_stage in ("A", "B", "C"):
            session["last_relationship_stage"] = relationship_stage
        
        # 增加轮次
        session["turn_count"] = session.get("turn_count", 0) + 1
        
        self._session_cache[user_id] = session
    
    def get_condition(self, user_id: int) -> str:
        """获取用户的实验条件（从用户数据读取）"""
        # 优先从用户数据库读取
        user = self.storage.get_user_by_id(user_id)
        if user and user.get("self_disclosure_condition"):
            return user.get("self_disclosure_condition")
        # 回退到session缓存
        session = self.get_or_create_session(user_id)
        return session.get("self_disclosure_condition", "emotional")
    
    def set_condition(self, user_id: int, condition: str):
        """设置用户的实验条件（持久化到用户数据）"""
        if condition not in ("emotional", "factual", "none"):
            condition = "emotional"
        # 更新用户数据库
        self.storage.update_user(user_id, {"self_disclosure_condition": condition})
        # 同时更新session缓存
        session = self.get_or_create_session(user_id)
        session["self_disclosure_condition"] = condition
    
    def reset_session(self, user_id: int):
        """重置用户会话（新对话开始时调用）"""
        self._session_cache.pop(user_id, None)


# 单例
_session_state: Optional[SessionStateService] = None

def get_session_state_service() -> SessionStateService:
    global _session_state
    if _session_state is None:
        _session_state = SessionStateService()
    return _session_state


def get_session_state() -> SessionStateService:
    """兼容旧引用名称。"""
    return get_session_state_service()

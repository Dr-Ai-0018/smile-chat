"""
SessionStateService - 维护短期状态
计算 preset（动态状态参数）供每轮对话使用
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from storage import JsonStorage


@dataclass
class SessionPreset:
    """动态状态参数（传给LLM的preset）"""
    recent_self_disclosure_rate: float  # 最近5条assistant中触发表露的比例
    last_relationship_stage: str  # 上一轮关系阶段 A/B/C
    conversation_duration_min: int  # 本轮对话持续分钟数
    local_time_bucket: str  # morning/afternoon/evening/late_night
    turn_count: int  # 本会话轮次
    
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
        
        # 初始化新会话
        session = {
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
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
        
        # 1. 计算 recent_self_disclosure_rate
        disclosure_rate = self._compute_disclosure_rate(user_id)
        
        # 2. 获取 last_relationship_stage
        last_stage = session.get("last_relationship_stage", "A")
        
        # 3. 计算 conversation_duration_min
        start_time_str = session.get("start_time")
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str)
                duration = (datetime.now() - start_time).total_seconds() / 60
                duration_min = int(duration // 5) * 5  # 精度5分钟
            except Exception:
                duration_min = 0
        else:
            duration_min = 0
        
        # 4. 计算 local_time_bucket
        time_bucket = self._get_time_bucket()
        
        # 5. 获取 turn_count
        turn_count = session.get("turn_count", 0)
        
        return SessionPreset(
            recent_self_disclosure_rate=disclosure_rate,
            last_relationship_stage=last_stage,
            conversation_duration_min=duration_min,
            local_time_bucket=time_bucket,
            turn_count=turn_count,
        )
    
    def _compute_disclosure_rate(self, user_id: int) -> float:
        """计算最近5条assistant消息的自我表露率"""
        # 从存储获取最近的聊天历史
        history = self.storage.get_chat_history(user_id=user_id, limit=20)
        
        # 筛选assistant消息
        assistant_msgs = [m for m in history if m.get("role") == "assistant"]
        recent_5 = assistant_msgs[-5:] if len(assistant_msgs) >= 5 else assistant_msgs
        
        if not recent_5:
            return 0.0
        
        # 统计触发表露的条数（兼容两种字段名）
        disclosure_count = sum(
            1 for m in recent_5 
            if m.get("meta", {}).get("did_self_disclosure", False)
            or m.get("meta", {}).get("self_disclosure_triggered", False)
        )
        
        return disclosure_count / len(recent_5)
    
    def _get_time_bucket(self) -> str:
        """获取当前时间段"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
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

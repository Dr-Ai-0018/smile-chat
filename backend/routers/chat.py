"""
聊天路由 - AI对话功能
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pathlib import Path
import json
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel

from routers.user import get_current_user
from models.schemas import ChatResponse
from services.ai_service import AIService
from storage import JsonStorage

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

# 实验参数默认值（可被 settings.json 覆盖）
MIN_USER_MESSAGE_LENGTH = int(os.getenv("MIN_USER_MESSAGE_LENGTH", "10"))
ROUND_RESET_INTERVAL_MINUTES = int(os.getenv("ROUND_RESET_INTERVAL_MINUTES", "20"))
MIN_ROUNDS_FOR_CHECKIN = int(os.getenv("MIN_ROUNDS_FOR_CHECKIN", "10"))
CHECKIN_PENDING_EXPIRE_HOURS = int(os.getenv("CHECKIN_PENDING_EXPIRE_HOURS", "4"))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)

router = APIRouter()
ai_service = AIService()
storage = JsonStorage()

# Memory文件系统路径
MEMORY_DIR = Path(__file__).parent.parent.parent / "memory" / "本体"

# 记录用户最后活跃时间和消息计数（用于自动压缩）
user_activity = {}
# 记录用户的当前聊天请求，用于新消息到来时主动取消旧请求
active_request_events = {}


def _runtime_setting_int(key: str, default: int) -> int:
    settings = storage.get_settings()
    try:
        return int(settings.get(key, default))
    except Exception:
        return default


def register_request(user_id: int) -> asyncio.Event:
    """为用户注册一个新的取消事件，并中断旧请求"""
    old_event = active_request_events.get(user_id)
    if old_event:
        old_event.set()
    
    new_event = asyncio.Event()
    active_request_events[user_id] = new_event
    return new_event

def clear_request(user_id: int, event: asyncio.Event):
    """清理已完成的请求事件，避免误伤后续请求"""
    current = active_request_events.get(user_id)
    if current is event:
        active_request_events.pop(user_id, None)

def get_user_memory_dir(user_id: int) -> Path:
    """获取用户记忆目录，确保目录结构存在"""
    user_dir = MEMORY_DIR / str(user_id)
    # 创建所有必需的子目录
    (user_dir / "history").mkdir(parents=True, exist_ok=True)
    (user_dir / "json").mkdir(parents=True, exist_ok=True)
    (user_dir / "memory").mkdir(parents=True, exist_ok=True)
    return user_dir

def save_message_to_history(user_id: int, role: str, content: str, image: str = None):
    """将消息保存到history文件"""
    user_dir = get_user_memory_dir(user_id)
    history_dir = user_dir / "history"
    
    # 使用中国时间的日期作为文件名，每天一个文件
    china_now = get_china_now()
    today = china_now.strftime("%Y-%m-%d")
    history_file = history_dir / f"{today}.txt"
    
    # 构建消息内容 - 使用中国时间
    timestamp = china_now.strftime("%H:%M:%S")
    role_name = "用户" if role == "user" else "启明"
    
    # 如果有图片，标注
    msg_content = content or ""
    if image:
        msg_content = "[图片] " + msg_content
    
    line = f"[{timestamp}] {role_name}: {msg_content}\n"
    
    # 追加到文件
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(line)

def update_json_memory(user_id: int, key: str, value):
    """更新用户的JSON记忆"""
    user_dir = get_user_memory_dir(user_id)
    json_file = user_dir / "json" / "memory.json"
    
    # 读取现有JSON
    data = {}
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    
    # 更新
    data[key] = value
    data["last_updated"] = get_china_now().isoformat()
    
    # 保存
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class MessageItem(BaseModel):
    role: str
    content: Optional[str] = ""
    image: Optional[str] = None

class SendMessageRequest(BaseModel):
    messages: List[MessageItem]

class LegacySendRequest(BaseModel):
    content: str

@router.post("/send_with_context", response_model=ChatResponse, response_model_exclude_none=True)
async def send_message_with_context(
    request: SendMessageRequest,
    user_id: int = Depends(get_current_user)
):
    """发送消息（带完整上下文，支持图片）"""
    cancel_event = register_request(user_id)
    
    # 获取最后一条用户消息
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="没有用户消息")
    
    last_user_msg = user_messages[-1]
    
    # 保存用户消息到JSON聊天历史
    storage.append_chat_message(
        user_id=user_id,
        role="user",
        content=last_user_msg.content or "",
        image=last_user_msg.image,
    )
    
    # 同时保存到Memory文件系统
    save_message_to_history(user_id, "user", last_user_msg.content or "", last_user_msg.image)

    # 收到用户消息时：记录时间、判断是否超时重置（不累加轮次，等AI成功回复后再+1）
    user_msg_time = get_china_now()
    _record_user_msg_time(user_id, last_user_msg.content or "", user_msg_time)

    context_config = ai_service.refresh_context_config()
    context_limit = int(context_config.get("max_messages", 80) or 80)

    # 由服务端统一基于持久化历史组装上下文，避免前端裁剪影响实际配置
    context_messages = [
        {
            "role": item.get("role"),
            "content": item.get("content", "") or "",
            "image": item.get("image"),
        }
        for item in storage.get_chat_history(user_id=user_id, limit=context_limit)
    ]

    try:
        # 调用AI服务 (使用v2协议化接口)
        response = await ai_service.chat_with_context_v2(
            messages=context_messages,
            user_id=user_id,
            cancel_event=cancel_event
        )
        
        if cancel_event.is_set():
            raise asyncio.CancelledError("请求被新的消息中断")
        
        reply_content = response.get("reply", response.get("content", ""))
        reply = response.get("reply") or reply_content
        segments = response.get("segments") or ([reply] if reply else [])
        meta = response.get("meta", {})

        # 保存AI回复到JSON聊天历史：按 segments 分条存储，避免刷新后合并
        total_segments = len(segments) if isinstance(segments, list) else 0
        if not isinstance(segments, list) or total_segments == 0:
            segments = [reply_content] if reply_content else []
            total_segments = len(segments)

        ts = get_china_now().isoformat()
        for idx, seg in enumerate(segments):
            seg_text = (str(seg) if seg is not None else "").strip()
            if seg_text.endswith("。"):
                seg_text = seg_text[:-1]
            if not seg_text:
                continue

            seg_meta = dict(meta) if isinstance(meta, dict) else {}
            seg_meta["segment_index"] = idx
            seg_meta["segment_total"] = total_segments

            storage.append_chat_message(
                user_id=user_id,
                role="assistant",
                content=seg_text,
                timestamp=ts,
                meta=seg_meta,
            )

            save_message_to_history(user_id, "assistant", seg_text)
        
        # 自动记忆压缩逻辑
        await check_and_compress_memory(user_id)

        # AI完整回复成功后才累加轮次，并记录本次会话最后活跃时间
        _increment_round_count(user_id, last_user_msg.content or "", user_msg_time)
        storage.update_user_experiment_state(user_id, {
            "last_session_end_time": get_china_now().isoformat(),
        })

        return ChatResponse(
            role="assistant",
            content=reply_content,
            timestamp=get_china_now(),
            reply=reply,
            segments=segments,
            meta=meta,
        )
    except asyncio.CancelledError:
        raise HTTPException(status_code=499, detail="请求已被新的消息取消")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI服务错误: {str(e)}")
    finally:
        clear_request(user_id, cancel_event)

async def check_and_compress_memory(user_id: int):
    """检查并执行自动记忆压缩"""
    now = get_china_now()
    
    # 获取或初始化用户活动记录
    if user_id not in user_activity:
        user_activity[user_id] = {
            "last_active": now,
            "msg_since_compress": 0,
            "last_compress": None
        }
    
    activity = user_activity[user_id]
    activity["msg_since_compress"] += 1
    
    # 计算距离上次活跃的时间
    time_since_last = (now - activity["last_active"]).total_seconds()
    activity["last_active"] = now
    
    should_compress = False
    
    # 情况1：聊了很久没说话（超过2小时），且有超过10条消息
    if time_since_last > 7200 and activity["msg_since_compress"] >= 10:
        should_compress = True
    
    # 情况2：频繁聊天，达到压缩阈值
    # 根据聊天频率动态调整阈值
    manual_threshold = storage.get_settings().get("memory_compress_threshold", 0)
    if manual_threshold and manual_threshold > 0:
        compress_threshold = manual_threshold
    elif time_since_last < 300:  # 5分钟内持续聊天
        compress_threshold = 40  # 高频聊天，40条压缩一次
    elif time_since_last < 1800:  # 30分钟内
        compress_threshold = 30
    else:
        compress_threshold = 20  # 低频聊天，20条压缩一次
    
    if activity["msg_since_compress"] >= compress_threshold:
        should_compress = True
    
    # 执行压缩
    if should_compress:
        try:
            msg_count = activity["msg_since_compress"]
            if msg_count <= 0:
                return

            history_items = storage.get_chat_history(user_id=user_id, limit=msg_count)
            messages_to_compress = [
                {"role": item.get("role"), "content": item.get("content", "")}
                for item in history_items
            ]
            
            # 异步压缩（不阻塞响应）
            asyncio.create_task(
                ai_service.compress_and_merge_memory(user_id, messages_to_compress)
            )
            
            # 重置计数
            activity["msg_since_compress"] = 0
            activity["last_compress"] = now
        except Exception as e:
            print(f"自动压缩记忆失败: {e}")

@router.get("/history")
async def get_history(
    limit: int = 100,
    user_id: int = Depends(get_current_user)
):
    """获取聊天历史"""
    history = storage.get_chat_history(user_id=user_id, limit=limit)
    return {"history": history}

# 保留旧的send接口兼容
@router.post("/send", response_model=ChatResponse, response_model_exclude_none=True)
async def send_message(
    content: Optional[str] = Query(default=None),
    body: Optional[LegacySendRequest] = Body(default=None),
    user_id: int = Depends(get_current_user)
):
    """发送聊天消息（旧接口，兼容）"""
    content_value = content
    if content_value is None and body is not None:
        content_value = body.content
    if content_value is None:
        raise HTTPException(status_code=400, detail="缺少content")
    request = SendMessageRequest(messages=[MessageItem(role="user", content=content_value)])
    return await send_message_with_context(request, user_id)


def _record_user_msg_time(user_id: int, user_msg_content: str, msg_time: datetime):
    """收到用户消息时调用：判断间隔是否超时，超时则重置轮次；不累加轮次。"""
    state = storage.get_user_experiment_state(user_id)
    last_time_str = state.get("last_user_message_time")
    min_rounds_for_checkin = _runtime_setting_int("min_rounds_for_checkin", MIN_ROUNDS_FOR_CHECKIN)
    pending_expire_hours = _runtime_setting_int(
        "checkin_pending_expire_hours",
        _runtime_setting_int("checkin_cooldown_hours", CHECKIN_PENDING_EXPIRE_HOURS),
    )
    pending_expire_minutes = max(1, pending_expire_hours * 60)
    base_reset_minutes = max(1, min(_runtime_setting_int("round_reset_interval_minutes", ROUND_RESET_INTERVAL_MINUTES), 20))
    round_count = int(state.get("current_round_count", 0) or 0)
    # 达到可打卡条件后，轮次间隔窗口切换为 4 小时（优先级高于 20 分钟规则）
    round_reset_interval_minutes = pending_expire_minutes if round_count >= min_rounds_for_checkin else base_reset_minutes

    if last_time_str:
        try:
            last_time = datetime.fromisoformat(last_time_str)
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=CHINA_TZ)
            gap_minutes = (msg_time - last_time).total_seconds() / 60
            if gap_minutes > round_reset_interval_minutes:
                # 超时：清零，记录新会话开始时间，但本轮轮次等AI回复后再+1
                storage.update_user_experiment_state(user_id, {
                    "current_round_count": 0,
                    "session_start_time": msg_time.isoformat(),
                    "last_user_message_time": msg_time.isoformat(),
                    "checkin_eligible_last_message_time": None,
                })
                return
        except Exception:
            pass

    # 所有用户消息都会刷新会话间隔判断时间；是否计轮仍由 AI 成功回复后 +
    # 1 且消息长度达标来决定。
    updates = {"last_user_message_time": msg_time.isoformat()}
    if not state.get("session_start_time"):
        updates["session_start_time"] = msg_time.isoformat()
    if round_count >= min_rounds_for_checkin:
        # 用于“可打卡但未打卡超过 4 小时自动失效”的计时锚点
        updates["checkin_eligible_last_message_time"] = msg_time.isoformat()
    storage.update_user_experiment_state(user_id, updates)


def _increment_round_count(user_id: int, user_msg_content: str, msg_time: datetime):
    """AI完整回复成功后调用：轮次 +1。"""
    min_user_message_length = _runtime_setting_int("min_user_message_length", MIN_USER_MESSAGE_LENGTH)
    if len(user_msg_content.strip()) < min_user_message_length:
        return
    state = storage.get_user_experiment_state(user_id)
    new_count = state.get("current_round_count", 0) + 1
    min_rounds_for_checkin = _runtime_setting_int("min_rounds_for_checkin", MIN_ROUNDS_FOR_CHECKIN)
    updates = {"current_round_count": new_count}
    if new_count >= min_rounds_for_checkin:
        updates["checkin_eligible_last_message_time"] = msg_time.isoformat()
    else:
        updates["checkin_eligible_last_message_time"] = None
    storage.update_user_experiment_state(user_id, updates)


# 保留旧名称供外部兼容（实际已不使用）
def update_round_count(user_id: int, user_msg_content: str, msg_time: datetime):
    _record_user_msg_time(user_id, user_msg_content, msg_time)
    _increment_round_count(user_id, user_msg_content, msg_time)

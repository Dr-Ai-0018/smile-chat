"""
聊天路由 - AI对话功能
"""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from pydantic import BaseModel

from routers.user import get_current_user
from models.schemas import ChatResponse
from services.ai_service import AIService
from storage import JsonStorage

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

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
    
    # DEBUG: 打印收到的消息
    for i, m in enumerate(request.messages):
        if m.image:
            img_len = len(m.image) if m.image else 0
            img_preview = m.image[:100] if m.image else "None"
            print(f"[DEBUG ROUTER] Message {i}: role={m.role}, has_image=True, image_len={img_len}")
            print(f"[DEBUG ROUTER] Image preview: {img_preview}...")
    
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
    
    try:
        # 调用AI服务 (使用v2协议化接口)
        response = await ai_service.chat_with_context_v2(
            messages=[m.model_dump() for m in request.messages],
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
    if time_since_last < 300:  # 5分钟内持续聊天
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

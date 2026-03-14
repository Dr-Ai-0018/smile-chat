"""
提示系统路由 - 管理员配置提示组、用户触发与回答
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)

from routers.user import get_current_user
from routers.admin import is_admin
from storage import JsonStorage

router = APIRouter()
storage = JsonStorage()


# ==================== Pydantic Models ====================
class PromptContent(BaseModel):
    title: str = ""
    body: str = ""


class PromptQuestion(BaseModel):
    kind: str = "ack"  # ack, choice_single, choice_multi, text
    required: bool = False
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    submit_text: str = "确定"


class PromptGroupCreate(BaseModel):
    type: str = "daily"  # daily, survey, feedback
    name: str
    enabled: bool = True
    threshold: int = 10
    frequency_mode: str = "once"  # once, repeat_every_n
    repeat_every_n: Optional[int] = None
    max_times: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    priority: int = 0
    content: PromptContent
    question: Optional[PromptQuestion] = None


class PromptGroupUpdate(BaseModel):
    type: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    threshold: Optional[int] = None
    frequency_mode: Optional[str] = None
    repeat_every_n: Optional[int] = None
    max_times: Optional[int] = None
    cooldown_seconds: Optional[int] = None
    priority: Optional[int] = None
    content: Optional[PromptContent] = None
    question: Optional[PromptQuestion] = None


class EvaluateRequest(BaseModel):
    since_reset_user_message_count: int


class PromptShownRequest(BaseModel):
    client_request_id: str
    chat_count_snapshot: int = 0


class PromptAnswerRequest(BaseModel):
    client_request_id: str
    answer: Dict[str, Any]
    chat_count_snapshot: int = 0


class PromptSkipRequest(BaseModel):
    client_request_id: str
    chat_count_snapshot: int = 0


class ResetCounterRequest(BaseModel):
    prompt_group_id: Optional[int] = None


# ==================== Admin Endpoints ====================
@router.get("/admin/prompt-groups")
async def list_prompt_groups(
    include_deleted: bool = False,
    admin_id: int = Depends(is_admin),
):
    """获取所有提示组"""
    groups = storage.get_prompt_groups(include_deleted=include_deleted)
    return {"prompt_groups": groups}


@router.post("/admin/prompt-groups")
async def create_prompt_group(
    req: PromptGroupCreate,
    admin_id: int = Depends(is_admin),
):
    """创建提示组"""
    group_data = req.model_dump()
    if group_data.get("content"):
        group_data["content"] = dict(group_data["content"])
    if group_data.get("question"):
        group_data["question"] = dict(group_data["question"])
    group = storage.create_prompt_group(group_data)
    return {"prompt_group": group}


@router.get("/admin/prompt-groups/{group_id}")
async def get_prompt_group(
    group_id: int,
    admin_id: int = Depends(is_admin),
):
    """获取单个提示组"""
    group = storage.get_prompt_group_by_id(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="提示组不存在")
    return {"prompt_group": group}


@router.put("/admin/prompt-groups/{group_id}")
async def update_prompt_group(
    group_id: int,
    req: PromptGroupUpdate,
    admin_id: int = Depends(is_admin),
):
    """更新提示组"""
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if "content" in updates and updates["content"]:
        updates["content"] = dict(updates["content"])
    if "question" in updates and updates["question"]:
        updates["question"] = dict(updates["question"])
    group = storage.update_prompt_group(group_id, updates)
    if not group:
        raise HTTPException(status_code=404, detail="提示组不存在")
    return {"prompt_group": group}


@router.delete("/admin/prompt-groups/{group_id}")
async def delete_prompt_group(
    group_id: int,
    hard: bool = False,
    admin_id: int = Depends(is_admin),
):
    """删除提示组（默认软删除）"""
    ok = storage.delete_prompt_group(group_id, hard=hard)
    if not ok:
        raise HTTPException(status_code=404, detail="提示组不存在")
    return {"message": "提示组已删除"}


@router.get("/admin/prompt-events")
async def list_prompt_events(
    user_id: Optional[int] = None,
    group_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    admin_id: int = Depends(is_admin),
):
    """查看提示事件日志"""
    events = storage.get_prompt_events(
        user_id=user_id,
        group_id=group_id,
        event_type=event_type,
        limit=limit,
    )
    return {"events": events}


@router.get("/admin/prompt-stats")
async def get_prompt_stats(
    admin_id: int = Depends(is_admin),
):
    """获取提示系统统计"""
    groups = storage.get_prompt_groups(include_deleted=False)
    stats = []
    for group in groups:
        group_id = group.get("id")
        shown_events = storage.get_prompt_events(group_id=group_id, event_type="shown", limit=10000)
        answered_events = storage.get_prompt_events(group_id=group_id, event_type="answered", limit=10000)
        skipped_events = storage.get_prompt_events(group_id=group_id, event_type="skipped", limit=10000)
        
        shown_users = set(e.get("user_id") for e in shown_events)
        answered_users = set(e.get("user_id") for e in answered_events)
        
        stats.append({
            "group_id": group_id,
            "group_name": group.get("name"),
            "group_type": group.get("type"),
            "shown_count": len(shown_events),
            "shown_users": len(shown_users),
            "answered_count": len(answered_events),
            "answered_users": len(answered_users),
            "skipped_count": len(skipped_events),
            "conversion_rate": len(answered_events) / len(shown_events) if shown_events else 0,
        })
    return {"stats": stats}


@router.get("/admin/prompt-groups/{group_id}/answers")
async def get_prompt_answers(
    group_id: int,
    limit: int = 100,
    admin_id: int = Depends(is_admin),
):
    """获取某提示组的所有回答"""
    events = storage.get_prompt_events(group_id=group_id, event_type="answered", limit=limit)
    answers = []
    for e in events:
        user = storage.get_user_by_id(e.get("user_id"))
        answers.append({
            "event_id": e.get("id"),
            "user_id": e.get("user_id"),
            "username": user.get("username") if user else None,
            "answer": e.get("answer"),
            "created_at": e.get("created_at"),
        })
    return {"answers": answers}


# ==================== User Endpoints ====================
@router.post("/prompts/evaluate")
async def evaluate_prompts(
    req: EvaluateRequest,
    user_id: int = Depends(get_current_user),
):
    """
    前端上报当前用户消息计数，后端判断是否需要触发提示。
    返回需要展示的提示列表（可能多个，前端按优先级展示）。
    """
    groups = storage.get_prompt_groups(include_deleted=False)
    prompts_to_show = []
    
    # 获取后端实际的用户消息数
    total_user_msg_count = 0
    chat_history_path = storage._chat_history_file(user_id)
    chat_data = storage.read_json(chat_history_path, {"next_id": 1, "items": []})
    for m in chat_data.get("items", []):
        if m.get("role") == "user":
            total_user_msg_count += 1
    
    now = get_china_now()
    
    for group in groups:
        if not group.get("enabled"):
            continue
        
        group_id = group.get("id")
        threshold = group.get("threshold", 10)
        frequency_mode = group.get("frequency_mode", "once")
        max_times = group.get("max_times")
        cooldown_seconds = group.get("cooldown_seconds")
        
        # 获取用户在此提示组的状态
        state = storage.get_user_prompt_state(user_id, group_id)
        if state is None:
            # 关键：新建提示组对“所有用户”都应从 0 开始计数。
            # 对于已有大量历史消息的老用户，如果 baseline 默认为 0，会导致一进入就立即触发。
            # 因此首次遇到该 group 时，将当前总用户消息数作为 baseline。
            state = {
                "times_triggered": 0,
                "times_shown": 0,
                "times_answered": 0,
                "last_shown_at": None,
                "completed": False,
                "last_reset_msg_count": total_user_msg_count,
            }
            storage.upsert_user_prompt_state(user_id, group_id, state)
        else:
            # 兼容修复：如果在旧版本中 state 创建时 baseline 默认为 0，
            # 会导致老用户（有历史消息）立刻触发。
            # 对于“还没有触发/展示过”的初始态，我们将 baseline 回填为当前总消息数。
            last_reset = state.get("last_reset_msg_count")
            if (last_reset is None or last_reset == 0) and state.get("times_triggered", 0) == 0 and state.get("times_shown", 0) == 0:
                state["last_reset_msg_count"] = total_user_msg_count
                storage.upsert_user_prompt_state(user_id, group_id, {
                    "last_reset_msg_count": total_user_msg_count,
                })
        
        # 如果已完成（once模式下回答过）则跳过
        if state.get("completed") and frequency_mode == "once":
            continue
        
        # 检查 max_times 限制
        if max_times is not None and state.get("times_shown", 0) >= max_times:
            continue
        
        # 检查冷却时间
        if cooldown_seconds and state.get("last_shown_at"):
            try:
                last_shown = datetime.fromisoformat(state["last_shown_at"])
                if (now - last_shown).total_seconds() < cooldown_seconds:
                    continue
            except:
                pass
        
        # 计算从上次重置后的消息数
        last_reset = state.get("last_reset_msg_count", 0)
        msg_since_reset = total_user_msg_count - last_reset
        
        # 判断是否达到阈值
        should_trigger = False
        if frequency_mode == "once":
            # once模式：达到阈值且未展示过
            if msg_since_reset >= threshold and state.get("times_shown", 0) == 0:
                should_trigger = True
        elif frequency_mode == "repeat_every_n":
            # 重复模式：每隔 threshold 条触发
            repeat_n = group.get("repeat_every_n") or threshold
            times_triggered = state.get("times_triggered", 0)
            next_trigger_at = threshold + times_triggered * repeat_n
            if msg_since_reset >= next_trigger_at:
                should_trigger = True
        
        if should_trigger:
            prompts_to_show.append({
                "prompt_group_id": group_id,
                "type": group.get("type"),
                "name": group.get("name"),
                "priority": group.get("priority", 0),
                "content": group.get("content"),
                "question": group.get("question"),
            })
    
    # 按优先级排序（高优先级在前）
    prompts_to_show.sort(key=lambda x: -x.get("priority", 0))
    
    return {
        "prompts_to_show": prompts_to_show,
        "server_msg_count": total_user_msg_count,
    }


@router.post("/prompts/{group_id}/shown")
async def record_prompt_shown(
    group_id: int,
    req: PromptShownRequest,
    user_id: int = Depends(get_current_user),
):
    """记录提示已展示"""
    group = storage.get_prompt_group_by_id(group_id)
    if not group or group.get("deleted"):
        raise HTTPException(status_code=404, detail="提示组不存在")
    
    # 幂等检查
    if storage.check_duplicate_event(req.client_request_id):
        return {"message": "已记录", "duplicate": True}
    
    # 记录事件
    storage.append_prompt_event(
        user_id=user_id,
        group_id=group_id,
        event_type="shown",
        chat_count_snapshot=req.chat_count_snapshot,
        client_request_id=req.client_request_id,
    )
    
    # 更新用户状态
    now = get_china_now().isoformat()
    state = storage.get_user_prompt_state(user_id, group_id) or {}
    storage.upsert_user_prompt_state(user_id, group_id, {
        "times_shown": state.get("times_shown", 0) + 1,
        "times_triggered": state.get("times_triggered", 0) + 1,
        "last_shown_at": now,
    })
    
    return {"message": "已记录展示", "duplicate": False}


@router.post("/prompts/{group_id}/answer")
async def submit_prompt_answer(
    group_id: int,
    req: PromptAnswerRequest,
    user_id: int = Depends(get_current_user),
):
    """提交提示回答"""
    group = storage.get_prompt_group_by_id(group_id)
    if not group or group.get("deleted"):
        raise HTTPException(status_code=404, detail="提示组不存在")
    
    # 幂等检查
    if storage.check_duplicate_event(req.client_request_id):
        return {"message": "已记录", "duplicate": True}
    
    # 记录事件
    storage.append_prompt_event(
        user_id=user_id,
        group_id=group_id,
        event_type="answered",
        chat_count_snapshot=req.chat_count_snapshot,
        answer=req.answer,
        client_request_id=req.client_request_id,
    )
    
    # 更新用户状态
    state = storage.get_user_prompt_state(user_id, group_id) or {}
    frequency_mode = group.get("frequency_mode", "once")
    
    # 获取当前用户消息总数作为新的重置点
    total_user_msg_count = 0
    chat_data = storage.read_json(storage._chat_history_file(user_id), {"next_id": 1, "items": []})
    for m in chat_data.get("items", []):
        if m.get("role") == "user":
            total_user_msg_count += 1
    
    updates = {
        "times_answered": state.get("times_answered", 0) + 1,
        "last_reset_msg_count": total_user_msg_count,  # 回答后重置计数
    }
    if frequency_mode == "once":
        updates["completed"] = True
    
    storage.upsert_user_prompt_state(user_id, group_id, updates)
    
    return {"message": "回答已记录", "duplicate": False}


@router.post("/prompts/{group_id}/skip")
async def skip_prompt(
    group_id: int,
    req: PromptSkipRequest,
    user_id: int = Depends(get_current_user),
):
    """跳过/关闭提示"""
    group = storage.get_prompt_group_by_id(group_id)
    if not group or group.get("deleted"):
        raise HTTPException(status_code=404, detail="提示组不存在")
    
    # 幂等检查
    if storage.check_duplicate_event(req.client_request_id):
        return {"message": "已记录", "duplicate": True}
    
    # 记录事件
    storage.append_prompt_event(
        user_id=user_id,
        group_id=group_id,
        event_type="skipped",
        chat_count_snapshot=req.chat_count_snapshot,
        client_request_id=req.client_request_id,
    )
    
    # 获取当前用户消息总数作为新的重置点
    total_user_msg_count = 0
    chat_data = storage.read_json(storage._chat_history_file(user_id), {"next_id": 1, "items": []})
    for m in chat_data.get("items", []):
        if m.get("role") == "user":
            total_user_msg_count += 1
    
    # 更新用户状态：跳过也重置计数，避免立即再次触发
    state = storage.get_user_prompt_state(user_id, group_id) or {}
    storage.upsert_user_prompt_state(user_id, group_id, {
        "last_reset_msg_count": total_user_msg_count,
    })
    
    return {"message": "已跳过", "duplicate": False}


@router.post("/prompts/reset-counter")
async def reset_prompt_counter(
    req: ResetCounterRequest,
    user_id: int = Depends(get_current_user),
):
    """
    手动重置某用户的提示计数器（用于前端"开始新对话"等场景）。
    如果不指定 prompt_group_id，则重置所有。
    """
    # 获取当前用户消息总数
    total_user_msg_count = 0
    chat_data = storage.read_json(storage._chat_history_file(user_id), {"next_id": 1, "items": []})
    for m in chat_data.get("items", []):
        if m.get("role") == "user":
            total_user_msg_count += 1
    
    if req.prompt_group_id:
        storage.upsert_user_prompt_state(user_id, req.prompt_group_id, {
            "last_reset_msg_count": total_user_msg_count,
        })
    else:
        # 重置所有
        groups = storage.get_prompt_groups(include_deleted=False)
        for group in groups:
            storage.upsert_user_prompt_state(user_id, group.get("id"), {
                "last_reset_msg_count": total_user_msg_count,
            })
    
    return {"message": "计数器已重置", "new_baseline": total_user_msg_count}

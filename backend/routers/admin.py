"""
管理路由 - 用户管理、邀请码管理、查看用户数据
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import os
import secrets
import json
import io
import re
import zipfile
import shutil
from urllib.parse import quote
from datetime import datetime, timezone, timedelta

# 中国时区 UTC+8
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    """获取中国时间"""
    return datetime.now(CHINA_TZ)

from models.schemas import InviteCodeCreate, PasswordReset
from pydantic import BaseModel as PydanticBaseModel
from utils.password import hash_password
from routers.user import get_current_user
from storage import JsonStorage
from services.memory_service import get_memory_service
from services.ai_service import AIService
from services.prompt_manager import get_prompt_manager
from services.chat_logger import get_chat_logger
from services.session_state import get_session_state
from services.weekly_survey_service import (
    retract_weekly_survey_notices_for_week,
    sync_weekly_survey_records_for_user,
)

router = APIRouter()
storage = JsonStorage()
memory_service = get_memory_service()
ai_service = AIService()
prompt_manager = get_prompt_manager()
chat_logger = get_chat_logger()
session_state = get_session_state()

MEMORY_BASE_PATH = Path(__file__).parent.parent.parent / "memory" / "本体"
MEMORY_BACKUP_BASE_PATH = Path(__file__).parent.parent.parent / "memory" / "备份" / "用户记忆"
CONDITION_FILES = dict(prompt_manager.CONDITION_FILES)
MIN_USER_MESSAGE_LENGTH = int(os.getenv("MIN_USER_MESSAGE_LENGTH", "10"))
MIN_WEEKLY_CHECKINS_FOR_SURVEY = int(os.getenv("MIN_WEEKLY_CHECKINS_FOR_SURVEY", "2"))


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHINA_TZ)
        return dt
    except Exception:
        return None


def _week_key_from_iso(value: Optional[str]) -> Optional[str]:
    dt = _parse_iso(value)
    if not dt:
        return None
    return dt.strftime("%Y-W%W")


def _current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")


def _is_effective_assistant_message(message: dict) -> bool:
    if message.get("role") != "assistant":
        return False
    meta = message.get("meta") or {}
    segment_index = meta.get("segment_index")
    if segment_index is None:
        return True
    return segment_index == 0


def _safe_avg(values: List[float]) -> float:
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return 0.0
    return round(sum(nums) / len(nums), 2)


def _runtime_setting_int(key: str, default: int) -> int:
    settings = storage.get_settings()
    try:
        return int(settings.get(key, default))
    except Exception:
        return default


def _raw_data_protection_error(action: str) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail=f"实验原始数据保护已开启，当前不允许执行“{action}”。如需进入新阶段，请使用周清理或数据导出。",
    )


def _build_user_metrics(user: dict, *, log_limit: int = 200) -> dict:
    user_id = user.get("id")
    if not isinstance(user_id, int):
        return {}

    history = storage.get_chat_history(user_id=user_id, limit=0)
    checkins = storage.get_checkin_records(user_id)
    exp_state = storage.get_user_experiment_state(user_id)
    logs = chat_logger.get_paired_logs(user_id, limit=log_limit)
    prompt_events = storage.get_prompt_events(user_id=user_id, limit=100000)
    current_week = exp_state.get("current_week_key") or _current_week_key()

    user_messages = [m for m in history if m.get("role") == "user"]
    assistant_messages = [m for m in history if m.get("role") == "assistant"]
    effective_dialogues = [m for m in assistant_messages if _is_effective_assistant_message(m)]
    this_week_messages = [m for m in history if _week_key_from_iso(m.get("timestamp")) == current_week]
    this_week_effective_dialogues = [m for m in effective_dialogues if _week_key_from_iso(m.get("timestamp")) == current_week]
    this_week_checkins = [r for r in checkins if r.get("week_key") == current_week]
    parse_success_logs = [l for l in logs if l.get("parse_success") is True]
    latency_values = [l.get("latency_ms") for l in logs if isinstance(l.get("latency_ms"), (int, float))]

    return {
        "user_id": user_id,
        "username": user.get("username"),
        "condition": user.get("self_disclosure_condition", "none"),
        "created_at": user.get("created_at"),
        "message_count": len(history),
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
        "image_message_count": sum(1 for m in history if m.get("image")),
        "effective_dialogue_count": len(effective_dialogues),
        "this_week_message_count": len(this_week_messages),
        "this_week_effective_dialogue_count": len(this_week_effective_dialogues),
        "weekly_checkin_count": exp_state.get("weekly_checkin_count", 0),
        "required_weekly_checkins": _runtime_setting_int("min_weekly_checkins_for_survey", MIN_WEEKLY_CHECKINS_FOR_SURVEY),
        "total_checkin_count": len(checkins),
        "this_week_checkin_count": len(this_week_checkins),
        "avg_rounds_per_checkin": _safe_avg([r.get("round_count_at_checkin") for r in checkins]),
        "current_round_count": exp_state.get("current_round_count", 0),
        "last_user_message_time": exp_state.get("last_user_message_time"),
        "session_start_time": exp_state.get("session_start_time"),
        "last_session_end_time": exp_state.get("last_session_end_time"),
        "last_checkin_at": exp_state.get("last_checkin_at"),
        "current_week_key": current_week,
        "weekly_survey_popup_shown": exp_state.get("weekly_survey_popup_shown", False),
        "request_count": len(logs),
        "successful_request_count": len(parse_success_logs),
        "avg_latency_ms": _safe_avg(latency_values),
        "last_request_at": logs[0].get("timestamp") if logs else None,
        "prompt_event_count": len(prompt_events),
        "prompt_shown_count": sum(1 for e in prompt_events if e.get("event_type") == "shown"),
        "prompt_answered_count": sum(1 for e in prompt_events if e.get("event_type") == "answered"),
        "valid_user_message_count": sum(
            1
            for m in user_messages
            if len(str(m.get("content") or "").strip()) >= _runtime_setting_int("min_user_message_length", MIN_USER_MESSAGE_LENGTH)
        ),
    }


def _safe_read_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _safe_read_json(path: Path) -> Any:
    raw = _safe_read_text(path)
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {"_raw": raw}


def _build_user_export_payload(user_id: int) -> Dict[str, Any]:
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    sync_weekly_survey_records_for_user(user_id)

    memory_dir = MEMORY_BASE_PATH / str(user_id)
    history_dir = memory_dir / "history"
    ltm_file = memory_dir / "ltm" / "long_term_memory.txt"
    json_memory_file = memory_dir / "json" / "memory.json"
    logs_dir = memory_dir / "logs"

    history_files: List[Dict[str, Any]] = []
    if history_dir.exists():
        for file in sorted(history_dir.glob("*.txt")):
            history_files.append({
                "filename": file.name,
                "content": _safe_read_text(file),
            })

    raw_log_files: List[Dict[str, Any]] = []
    if logs_dir.exists():
        for file in sorted(logs_dir.glob("*.json")):
            raw_log_files.append({
                "filename": file.name,
                "content": _safe_read_json(file),
            })

    sanitized_user = {k: v for k, v in user.items() if k != "pwd_hash"}

    return {
        "user": sanitized_user,
        "metrics": _build_user_metrics(user, log_limit=0),
        "experiment_state": storage.get_user_experiment_state(user_id),
        "checkins": storage.get_checkin_records(user_id),
        "request_logs": chat_logger.get_paired_logs(user_id, limit=0),
        "prompt_events": storage.get_prompt_events(user_id=user_id, limit=100000),
        "prompt_states": storage.get_user_prompt_states(user_id),
        "notices": storage.get_inbox_notices_for_user(user_id),
        "notice_states": storage.get_user_notice_states(user_id),
        "weekly_surveys": storage.get_weekly_survey_records(user_id=user_id, limit=0),
        "history": storage.get_chat_history(user_id=user_id, limit=0),
        "memory": {
            "long_term": _safe_read_text(ltm_file),
            "json_memory": _safe_read_json(json_memory_file),
            "history_files": history_files,
            "raw_logs": raw_log_files,
        },
    }


def _create_memory_backup(
    user_id: int,
    *,
    action: str,
    admin_id: int,
    note: str = "",
) -> Dict[str, Any]:
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    memory_dir = MEMORY_BASE_PATH / str(user_id)
    backup_dir = MEMORY_BACKUP_BASE_PATH / str(user_id)
    backup_dir.mkdir(parents=True, exist_ok=True)

    now = get_china_now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"{timestamp}_{action}.zip"
    backup_path = backup_dir / backup_name

    include_dirs = ["ltm", "json", "memory", "history"]
    metadata = {
        "backup_type": "admin_memory_backup",
        "action": action,
        "user_id": user_id,
        "username": user.get("username"),
        "admin_id": admin_id,
        "created_at": now.isoformat(),
        "note": note,
        "source_dir": str(memory_dir),
        "included_sections": include_dirs,
    }

    with zipfile.ZipFile(backup_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        _zip_write_json(zip_file, "metadata.json", metadata)

        for section in include_dirs:
            source = memory_dir / section
            if source.is_file():
                zip_file.write(source, arcname=f"{section}/{source.name}")
                continue
            if not source.exists():
                continue
            for file in sorted(source.rglob("*")):
                if not file.is_file():
                    continue
                arcname = file.relative_to(memory_dir).as_posix()
                zip_file.write(file, arcname=arcname)

    return {
        "filename": backup_name,
        "path": str(backup_path),
        "created_at": now.isoformat(),
    }

# 管理员检查
def is_admin(user_id: int = Depends(get_current_user)):
    # 简单判断user_id为1是管理员
    # TODO: 实现更完善的角色系统
    if user_id != 1:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user_id

@router.get("/users")
async def list_users(
    admin_id: int = Depends(is_admin)
):
    """获取用户列表"""
    users = []
    for user in storage.read_users():
        user_id = user.get("id")
        if not isinstance(user_id, int):
            continue

        msg_count = storage.count_chat_messages(user_id)
        state = storage.get_user_experiment_state(user_id)
        users.append({
            "id": user_id,
            "username": user.get("username"),
            "avatar": user.get("avatar"),
            "created_at": user.get("created_at"),
            "message_count": msg_count,
            "condition": user.get("self_disclosure_condition", "none"),
            "weekly_checkin_count": state.get("weekly_checkin_count", 0),
        })

    return {
        "users": users,
        "threshold": _runtime_setting_int("min_weekly_checkins_for_survey", MIN_WEEKLY_CHECKINS_FOR_SURVEY),
    }

@router.get("/user/{user_id}/history")
async def get_user_history(
    user_id: int,
    limit: int = 100,
    admin_id: int = Depends(is_admin)
):
    """查看指定用户的聊天记录（管理员权限）"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    history = storage.get_chat_history(user_id=user_id, limit=limit)
    return {
        "user_id": user_id,
        "username": user.get("username"),
        "history": history
    }


@router.get("/user/{user_id}/detail")
async def get_user_detail(
    user_id: int,
    log_limit: int = 120,
    history_limit: int = 120,
    admin_id: int = Depends(is_admin),
):
    """获取用户详细信息、请求日志、打卡记录和提示事件"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    sync_weekly_survey_records_for_user(user_id)

    metrics = _build_user_metrics(user, log_limit=max(20, min(log_limit, 500)))
    history = storage.get_chat_history(user_id=user_id, limit=max(20, min(history_limit, 300)))
    checkins = storage.get_checkin_records(user_id)
    prompt_events = storage.get_prompt_events(user_id=user_id, limit=200)
    logs = chat_logger.get_paired_logs(user_id, limit=max(20, min(log_limit, 500)))
    weekly_surveys = storage.get_weekly_survey_records(user_id=user_id, limit=0)

    return {
        "user": {
            "id": user_id,
            "username": user.get("username"),
            "avatar": user.get("avatar"),
            "created_at": user.get("created_at"),
            "condition": user.get("self_disclosure_condition", "none"),
        },
        "metrics": metrics,
        "history": history,
        "checkins": checkins,
        "request_logs": logs,
        "prompt_events": prompt_events,
        "weekly_surveys": weekly_surveys,
    }

@router.get("/user/{user_id}/memory")
async def get_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """查看指定用户的记忆（管理员权限）"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    memory_dir = MEMORY_BASE_PATH / str(user_id)
    memory_data = {
        "long_term": "",
        "json_memory": {},
        "history_files": []
    }
    
    # 读取长期记忆（通过MemoryService）
    memory_data["long_term"] = memory_service.read_ltm_text(user_id)
    
    # 读取JSON记忆
    json_file = memory_dir / "json" / "memory.json"
    if json_file.exists():
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                memory_data["json_memory"] = json.load(f)
        except:
            pass
    
    # 列出历史文件
    history_dir = memory_dir / "history"
    if history_dir.exists():
        for file in sorted(history_dir.glob("*.txt"), reverse=True)[:10]:
            memory_data["history_files"].append({
                "name": file.name,
                "content": file.read_text(encoding="utf-8")[:500] + "..."
            })
    
    return {
        "user_id": user_id,
        "username": user.get("username"),
        "memory": memory_data
    }

@router.delete("/user/{user_id}/history")
async def clear_user_history(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """清空指定用户的聊天记录（管理员权限）"""
    raise _raw_data_protection_error("清空聊天记录")

@router.post("/create_invite")
async def create_invite_codes(
    req: InviteCodeCreate,
    admin_id: int = Depends(is_admin),
):
    """创建邀请码"""
    created: List[dict] = []

    if req.items:
        payload_items: List[Dict[str, str]] = []
        seen_codes = set()
        duplicate_codes = set()

        for item in req.items:
            code = item.code.strip()
            remark = (item.remark or "").strip()
            if not code:
                continue
            if code in seen_codes:
                duplicate_codes.add(code)
                continue
            seen_codes.add(code)
            payload_items.append({"code": code, "remark": remark})

        if duplicate_codes:
            duplicates_text = "、".join(sorted(duplicate_codes))
            raise HTTPException(status_code=400, detail=f"批量新增失败，存在重复邀请码: {duplicates_text}")

        if not payload_items:
            raise HTTPException(status_code=400, detail="请至少填写一个邀请码")

        created = storage.create_invite_codes(payload_items)
        created_codes = {item.get("code") for item in created if item.get("code")}
        skipped = [item["code"] for item in payload_items if item["code"] not in created_codes]
        return {
            "items": created,
            "codes": [c.get("code") for c in created if c.get("code")],
            "count": len(created),
            "skipped": skipped,
        }

    remaining = int(req.count or 0)
    if remaining < 1:
        raise HTTPException(status_code=400, detail="请提供生成数量，或填写自定义邀请码")
    while remaining > 0:
        batch = [secrets.token_urlsafe(16) for _ in range(remaining)]
        created_batch = storage.create_invite_codes(batch)
        created.extend(created_batch)
        remaining = req.count - len(created)

    codes = [c.get("code") for c in created if c.get("code")]
    return {"items": created, "codes": codes, "count": len(codes), "skipped": []}

@router.get("/invites")
async def list_invites(
    admin_id: int = Depends(is_admin),
):
    """获取邀请码列表"""
    invites = storage.read_invites()
    invites.sort(key=lambda x: ((x.get("created_at") or ""), int(x.get("id") or 0)), reverse=True)
    users_by_id = {}
    for user in storage.read_users():
        user_id = user.get("id")
        if isinstance(user_id, int):
            users_by_id[user_id] = user

    formatted = []
    for invite in invites:
        used_by = invite.get("used_by")
        used_user = users_by_id.get(used_by) if isinstance(used_by, int) else None
        formatted.append({
            "id": invite.get("id"),
            "code": invite.get("code"),
            "remark": invite.get("remark") or "",
            "used": bool(invite.get("used")),
            "used_by": used_by,
            "used_username": used_user.get("username") if used_user else None,
            "used_condition": used_user.get("self_disclosure_condition") if used_user else None,
            "created_at": invite.get("created_at"),
        })

    return {"invites": formatted}

@router.post("/reset_password")
async def reset_password(
    req: PasswordReset,
    admin_id: int = Depends(is_admin),
):
    """重置用户密码"""
    if not storage.get_user_by_id(req.user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    pwd_hash = hash_password(req.new_password)
    storage.update_user(req.user_id, {"pwd_hash": pwd_hash})
    
    return {"message": "密码重置成功"}

@router.post("/push")
async def push_message(
    message: str,
    admin_id: int = Depends(is_admin)
):
    """推送系统消息"""
    # TODO: 实现推送逻辑
    return {"message": "推送功能开发中"}

@router.get("/memory/all")
async def list_all_memory(
    admin_id: int = Depends(is_admin),
):
    """列出所有用户的记忆状态"""
    memory_list = []
    for user in storage.read_users():
        user_id = user.get("id")
        username = user.get("username")
        if not isinstance(user_id, int):
            continue
        memory_dir = MEMORY_BASE_PATH / str(user_id)
        
        user_memory = {
            "user_id": user_id,
            "username": username,
            "has_long_term": False,
            "has_json": False,
            "history_count": 0,
            "long_term_preview": ""
        }
        
        # 检查长期记忆（通过MemoryService）
        content = memory_service.read_ltm_text(user_id).strip()
        if content:
            user_memory["has_long_term"] = True
            user_memory["long_term_preview"] = content[:200] + "..." if len(content) > 200 else content
        
        # 检查JSON记忆
        json_file = memory_dir / "json" / "memory.json"
        if json_file.exists():
            user_memory["has_json"] = True
        
        # 统计历史文件数
        history_dir = memory_dir / "history"
        if history_dir.exists():
            user_memory["history_count"] = len(list(history_dir.glob("*.txt")))
        
        memory_list.append(user_memory)
    
    return {"memories": memory_list}

class MemoryUpdateRequest(BaseModel):
    content: str

@router.put("/user/{user_id}/memory/long_term")
async def update_user_long_term_memory(
    user_id: int,
    request: MemoryUpdateRequest,
    admin_id: int = Depends(is_admin),
):
    """更新用户长期记忆"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    backup = _create_memory_backup(
        user_id,
        action="edit_long_term",
        admin_id=admin_id,
        note="管理员编辑长期记忆前自动备份",
    )
    memory_service.write_ltm(user_id, request.content, {"admin_edit": True})

    return {"message": "记忆更新成功，已自动备份", "backup": backup}

@router.delete("/user/{user_id}/memory")
async def clear_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """清空用户所有记忆"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")

    backup = _create_memory_backup(
        user_id,
        action="clear_memory",
        admin_id=admin_id,
        note="管理员清空记忆前自动备份",
    )
    memory_dir = MEMORY_BASE_PATH / str(user_id)

    for section in ("history", "json", "memory", "ltm"):
        target = memory_dir / section
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
        target.mkdir(parents=True, exist_ok=True)

    return {"message": "记忆已清空，已自动备份", "backup": backup}

@router.get("/user/{user_id}/history_file/{filename}")
async def get_history_file(
    user_id: int,
    filename: str,
    admin_id: int = Depends(is_admin)
):
    """获取指定历史文件的完整内容"""
    history_file = MEMORY_BASE_PATH / str(user_id) / "history" / filename
    if not history_file.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return {"content": history_file.read_text(encoding="utf-8")}

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """删除用户及其所有数据"""
    raise _raw_data_protection_error("删除用户")

@router.get("/stats")
async def get_system_stats(
    admin_id: int = Depends(is_admin),
):
    """获取系统统计数据"""

    users = storage.read_users()
    user_count = len(users)

    today = get_china_now().date()
    msg_count = 0
    today_msg_count = 0
    active_users = 0
    condition_distribution = {"none": 0, "emotional": 0, "factual": 0}
    per_user_messages = []
    for user in users:
        uid = user.get("id")
        if not isinstance(uid, int):
            continue

        history = storage.get_chat_history(user_id=uid, limit=0)
        user_msg_count = len(history)
        msg_count += user_msg_count
        per_user_messages.append({
            "user_id": uid,
            "username": user.get("username"),
            "message_count": user_msg_count,
            "condition": user.get("self_disclosure_condition", "none"),
        })
        condition = user.get("self_disclosure_condition", "none")
        condition_distribution[condition] = condition_distribution.get(condition, 0) + 1

        has_today = False
        for item in history:
            ts = item.get("timestamp")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except Exception:
                continue
            if dt.date() == today:
                today_msg_count += 1
                has_today = True
        if has_today:
            active_users += 1

    available_invites = sum(1 for i in storage.read_invites() if not i.get("used"))
    
    return {
        "user_count": user_count,
        "message_count": msg_count,
        "today_messages": today_msg_count,
        "active_users_today": active_users,
        "available_invites": available_invites,
        "condition_distribution": condition_distribution,
        "per_user_messages": per_user_messages,
    }


@router.get("/stats/detailed")
async def get_detailed_system_stats(
    admin_id: int = Depends(is_admin),
):
    """获取详细统计数据：周维度、用户维度、请求与打卡汇总。"""
    users = [u for u in storage.read_users() if isinstance(u.get("id"), int)]
    metrics_list = [_build_user_metrics(user, log_limit=0) for user in users]
    all_checkins = storage.get_all_checkin_records()

    weekly_map: dict[str, dict] = {}
    for user in users:
        user_id = user["id"]
        username = user.get("username")
        history = storage.get_chat_history(user_id=user_id, limit=0)
        logs = chat_logger.get_paired_logs(user_id, limit=0)

        for msg in history:
            week_key = _week_key_from_iso(msg.get("timestamp"))
            if not week_key:
                continue
            bucket = weekly_map.setdefault(
                week_key,
                {
                    "week_key": week_key,
                    "message_count": 0,
                    "user_message_count": 0,
                    "assistant_message_count": 0,
                    "effective_dialogue_count": 0,
                    "active_user_ids": set(),
                    "checkin_count": 0,
                    "request_count": 0,
                    "successful_request_count": 0,
                },
            )
            bucket["message_count"] += 1
            bucket["active_user_ids"].add(user_id)
            if msg.get("role") == "user":
                bucket["user_message_count"] += 1
            elif msg.get("role") == "assistant":
                bucket["assistant_message_count"] += 1
                if _is_effective_assistant_message(msg):
                    bucket["effective_dialogue_count"] += 1

        for log in logs:
            week_key = _week_key_from_iso(log.get("timestamp"))
            if not week_key:
                continue
            bucket = weekly_map.setdefault(
                week_key,
                {
                    "week_key": week_key,
                    "message_count": 0,
                    "user_message_count": 0,
                    "assistant_message_count": 0,
                    "effective_dialogue_count": 0,
                    "active_user_ids": set(),
                    "checkin_count": 0,
                    "request_count": 0,
                    "successful_request_count": 0,
                },
            )
            bucket["request_count"] += 1
            bucket["active_user_ids"].add(user_id)
            if log.get("parse_success"):
                bucket["successful_request_count"] += 1

    for record in all_checkins:
        week_key = record.get("week_key")
        if not week_key:
            continue
        bucket = weekly_map.setdefault(
            week_key,
            {
                "week_key": week_key,
                "message_count": 0,
                "user_message_count": 0,
                "assistant_message_count": 0,
                "effective_dialogue_count": 0,
                "active_user_ids": set(),
                "checkin_count": 0,
                "request_count": 0,
                "successful_request_count": 0,
            },
        )
        bucket["checkin_count"] += 1
        if isinstance(record.get("user_id"), int):
            bucket["active_user_ids"].add(record["user_id"])

    weekly_stats = []
    for week_key, bucket in weekly_map.items():
        weekly_stats.append(
            {
                "week_key": week_key,
                "message_count": bucket["message_count"],
                "user_message_count": bucket["user_message_count"],
                "assistant_message_count": bucket["assistant_message_count"],
                "effective_dialogue_count": bucket["effective_dialogue_count"],
                "checkin_count": bucket["checkin_count"],
                "request_count": bucket["request_count"],
                "successful_request_count": bucket["successful_request_count"],
                "active_user_count": len(bucket["active_user_ids"]),
            }
        )
    weekly_stats.sort(key=lambda item: item["week_key"], reverse=True)

    total_requests = sum(item.get("request_count", 0) for item in metrics_list)
    total_success = sum(item.get("successful_request_count", 0) for item in metrics_list)
    total_effective_dialogues = sum(item.get("effective_dialogue_count", 0) for item in metrics_list)
    total_checkins = sum(item.get("total_checkin_count", 0) for item in metrics_list)

    return {
        "overview": {
            "user_count": len(users),
            "request_count": total_requests,
            "successful_request_count": total_success,
            "effective_dialogue_count": total_effective_dialogues,
            "checkin_count": total_checkins,
            "current_week_key": _current_week_key(),
            "current_week_checkin_count": len(storage.get_all_checkin_records(_current_week_key())),
            "current_week_active_user_count": sum(1 for item in metrics_list if item.get("this_week_message_count", 0) > 0),
            "avg_latency_ms": _safe_avg([item.get("avg_latency_ms") for item in metrics_list]),
        },
        "weekly": weekly_stats,
        "users": sorted(metrics_list, key=lambda item: item.get("message_count", 0), reverse=True),
    }


@router.post("/user/{user_id}/memory/compress")
async def compress_user_memory(
    user_id: int,
    admin_id: int = Depends(is_admin),
):
    """管理员手动触发用户记忆压缩"""
    if not storage.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        summary = await ai_service.compress_memory(user_id)
        return {"message": "记忆压缩成功", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记忆压缩失败: {str(e)}")


class WeeklyCleanupRequest(PydanticBaseModel):
    reset_checkins: bool = False


class WeeklySurveyRetractRequest(PydanticBaseModel):
    week_key: Optional[str] = None


class UserExportRequest(PydanticBaseModel):
    user_ids: List[int]


def _sanitize_export_name(value: str, fallback: str) -> str:
    text = (value or "").strip()
    if not text:
        text = fallback
    text = re.sub(r'[\\/:*?"<>|]+', "_", text)
    text = re.sub(r"\s+", " ", text).strip().rstrip(".")
    return text or fallback


def _zip_write_json(zip_file: zipfile.ZipFile, path: str, payload: Any) -> None:
    zip_file.writestr(
        path,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


@router.post("/checkin/weekly-cleanup")
async def trigger_weekly_cleanup(
    req: WeeklyCleanupRequest,
    admin_id: int = Depends(is_admin),
):
    """手动执行每周清理：至少清零当前轮次，可选同时清零本周打卡计数。"""
    updated = storage.reset_weekly_experiment_state(
        reset_checkins=req.reset_checkins,
        reset_week_key=req.reset_checkins,
    )
    return {
        "message": "每周清理已执行",
        "updated_users": updated,
        "reset_checkins": req.reset_checkins,
        "current_week_key": _current_week_key(),
    }


@router.post("/checkin/weekly-survey/retract")
async def retract_weekly_survey_dispatch(
    req: WeeklySurveyRetractRequest,
    admin_id: int = Depends(is_admin),
):
    """撤回指定周次已派发的周问卷通知，允许后续按规则重新派发。"""
    result = retract_weekly_survey_notices_for_week(req.week_key)
    return {
        "message": "周问卷派发状态已撤回",
        **result,
    }


@router.post("/users/export")
async def export_users_raw_data(
    req: UserExportRequest,
    admin_id: int = Depends(is_admin),
):
    """批量导出用户全量原始数据快照"""
    user_ids = []
    seen = set()
    for value in req.user_ids:
        try:
            user_id = int(value)
        except Exception:
            continue
        if user_id <= 0 or user_id in seen:
            continue
        seen.add(user_id)
        user_ids.append(user_id)

    if not user_ids:
        raise HTTPException(status_code=400, detail="至少选择一位用户")

    export_items = [_build_user_export_payload(user_id) for user_id in user_ids]
    return {
        "generated_at": get_china_now().isoformat(),
        "user_count": len(export_items),
        "users": export_items,
    }


@router.post("/users/export-zip")
async def export_users_zip(
    req: UserExportRequest,
    admin_id: int = Depends(is_admin),
):
    """将选中用户的原始数据按目录结构打包为 zip"""
    user_ids = []
    seen = set()
    for value in req.user_ids:
        try:
            user_id = int(value)
        except Exception:
            continue
        if user_id <= 0 or user_id in seen:
            continue
        seen.add(user_id)
        user_ids.append(user_id)

    if not user_ids:
        raise HTTPException(status_code=400, detail="至少选择一位用户")

    export_items = [_build_user_export_payload(user_id) for user_id in user_ids]
    generated_at = get_china_now().isoformat()
    filename = f"用户全量原始数据_{get_china_now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
    ascii_filename = f"user_export_{get_china_now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"

    archive_buffer = io.BytesIO()
    used_folder_names = set()

    with zipfile.ZipFile(archive_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        _zip_write_json(zip_file, "manifest.json", {
            "generated_at": generated_at,
            "user_count": len(export_items),
            "user_ids": user_ids,
        })

        for item in export_items:
            user = item.get("user") or {}
            user_id = int(user.get("id"))
            username = _sanitize_export_name(str(user.get("username") or ""), f"user_{user_id}")
            folder_name = f"{username}_{user_id}"
            if folder_name in used_folder_names:
                folder_name = f"{folder_name}_{len(used_folder_names) + 1}"
            used_folder_names.add(folder_name)

            base = f"{folder_name}/"
            _zip_write_json(zip_file, f"{base}user.json", item.get("user") or {})
            _zip_write_json(zip_file, f"{base}metrics.json", item.get("metrics") or {})
            _zip_write_json(zip_file, f"{base}experiment_state.json", item.get("experiment_state") or {})
            _zip_write_json(zip_file, f"{base}checkins.json", item.get("checkins") or [])
            _zip_write_json(zip_file, f"{base}request_logs.json", item.get("request_logs") or [])
            _zip_write_json(zip_file, f"{base}prompt_events.json", item.get("prompt_events") or [])
            _zip_write_json(zip_file, f"{base}prompt_states.json", item.get("prompt_states") or [])
            _zip_write_json(zip_file, f"{base}notices.json", item.get("notices") or [])
            _zip_write_json(zip_file, f"{base}notice_states.json", item.get("notice_states") or [])
            _zip_write_json(zip_file, f"{base}weekly_surveys.json", item.get("weekly_surveys") or [])
            _zip_write_json(zip_file, f"{base}chat_history.json", item.get("history") or [])

            memory = item.get("memory") or {}
            zip_file.writestr(f"{base}memory/long_term_memory.txt", memory.get("long_term") or "")
            _zip_write_json(zip_file, f"{base}memory/json_memory.json", memory.get("json_memory") or {})

            history_files = memory.get("history_files") or []
            for index, history_file in enumerate(history_files, start=1):
                raw_name = str((history_file or {}).get("filename") or f"history_{index}.txt")
                safe_name = _sanitize_export_name(raw_name, f"history_{index}.txt")
                if not safe_name.lower().endswith(".txt"):
                    safe_name = f"{safe_name}.txt"
                zip_file.writestr(
                    f"{base}memory/history_files/{safe_name}",
                    str((history_file or {}).get("content") or ""),
                )

            raw_logs = memory.get("raw_logs") or []
            for index, raw_log in enumerate(raw_logs, start=1):
                raw_name = str((raw_log or {}).get("filename") or f"log_{index}.json")
                safe_name = _sanitize_export_name(raw_name, f"log_{index}.json")
                if not safe_name.lower().endswith(".json"):
                    safe_name = f"{safe_name}.json"
                _zip_write_json(
                    zip_file,
                    f"{base}memory/raw_logs/{safe_name}",
                    (raw_log or {}).get("content") or {},
                )

    archive_buffer.seek(0)
    encoded_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{encoded_filename}",
        "X-Export-Filename": ascii_filename,
    }
    return StreamingResponse(archive_buffer, media_type="application/zip", headers=headers)

# ==================== 邀请码开关 ====================
class InviteCodeToggleRequest(PydanticBaseModel):
    enabled: bool

@router.get("/settings/invite_code")
async def get_invite_code_setting(
    admin_id: int = Depends(is_admin),
):
    """获取邀请码开关状态"""
    settings = storage.get_settings()
    return {
        "invite_code_enabled": settings.get("invite_code_enabled", True)
    }

@router.post("/settings/invite_code")
async def set_invite_code_setting(
    req: InviteCodeToggleRequest,
    admin_id: int = Depends(is_admin),
):
    """设置邀请码开关状态"""
    settings = storage.update_settings({"invite_code_enabled": req.enabled})
    return {
        "invite_code_enabled": settings.get("invite_code_enabled", True),
        "message": "邀请码已" + ("启用" if req.enabled else "关闭")
    }

# ==================== 通用设置 GET/PUT ====================
@router.get("/settings")
async def get_all_settings(admin_id: int = Depends(is_admin)):
    """获取所有系统设置"""
    return storage.prune_settings_keys(["experiment_pages_enabled"])

@router.put("/settings")
async def update_all_settings(
    updates: dict,
    admin_id: int = Depends(is_admin),
):
    """更新系统设置（部分更新）"""
    updates.pop("experiment_pages_enabled", None)
    storage.prune_settings_keys(["experiment_pages_enabled"])

    # 校验打卡题目数量
    if "checkin_questions" in updates:
        qs = updates["checkin_questions"]
        if not isinstance(qs, list) or len(qs) == 0:
            raise HTTPException(status_code=400, detail="打卡题目至少需要1题")
        updates["checkin_questions"] = [q for q in qs if isinstance(q, str) and q.strip()]
        if len(updates["checkin_questions"]) == 0:
            raise HTTPException(status_code=400, detail="打卡题目不能全为空")
    int_fields = {
        "memory_compress_threshold": (0, 10000),
        "chat_timer_duration_minutes": (1, 240),
        "min_rounds_for_checkin": (1, 1000),
        "checkin_cooldown_hours": (0, 168),
        "min_weekly_checkins_for_survey": (0, 50),
        "min_user_message_length": (1, 10000),
        "round_reset_interval_minutes": (1, 10080),
    }
    for key, (min_v, max_v) in int_fields.items():
        if key in updates:
            try:
                updates[key] = int(updates[key])
            except Exception:
                raise HTTPException(status_code=400, detail=f"{key} 必须是整数")
            if updates[key] < min_v or updates[key] > max_v:
                raise HTTPException(status_code=400, detail=f"{key} 必须在 {min_v}-{max_v} 之间")
    settings = storage.update_settings(updates)
    return settings


class SystemPromptUpdateRequest(PydanticBaseModel):
    content: str


class UserConditionUpdateRequest(PydanticBaseModel):
    condition: str


@router.put("/user/{user_id}/condition")
async def update_user_condition(
    user_id: int,
    request: UserConditionUpdateRequest,
    admin_id: int = Depends(is_admin),
):
    """管理员手动调整指定用户的系统提示词条件。只影响当前用户，不改变后续新用户分配逻辑。"""
    user = storage.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    condition = (request.condition or "").strip()
    if condition not in CONDITION_FILES:
        raise HTTPException(status_code=400, detail="无效的提示词条件")

    session_state.set_condition(user_id, condition)
    updated_user = storage.get_user_by_id(user_id) or user
    return {
        "message": "用户系统提示词条件已更新",
        "user_id": user_id,
        "username": updated_user.get("username"),
        "condition": updated_user.get("self_disclosure_condition", condition),
    }


@router.get("/system-prompts")
async def list_system_prompts(admin_id: int = Depends(is_admin)):
    """获取三套系统提示词的概览"""
    prompts = []
    for condition, filename in CONDITION_FILES.items():
        active_path = prompt_manager.get_active_prompt_path(condition)
        source = prompt_manager.get_prompt_source(condition)
        content = ""
        if active_path and active_path.exists():
            content = active_path.read_text(encoding="utf-8")
        prompts.append({
            "condition": condition,
            "filename": filename,
            "size": len(content),
            "lines": len(content.splitlines()) if content else 0,
            "preview": content[:200],
            "source": source,
        })
    return {"prompts": prompts}


@router.get("/system-prompts/{condition}")
async def get_system_prompt_content(
    condition: str,
    admin_id: int = Depends(is_admin),
):
    """获取指定条件的系统提示词全文"""
    filename = CONDITION_FILES.get(condition)
    if not filename:
        raise HTTPException(status_code=404, detail="提示词条件不存在")
    path = prompt_manager.get_active_prompt_path(condition)
    if path is None or not path.exists():
        raise HTTPException(status_code=404, detail="提示词文件不存在")
    return {
        "condition": condition,
        "filename": filename,
        "source": prompt_manager.get_prompt_source(condition),
        "content": path.read_text(encoding="utf-8"),
    }


@router.put("/system-prompts/{condition}")
async def update_system_prompt_content(
    condition: str,
    request: SystemPromptUpdateRequest,
    admin_id: int = Depends(is_admin),
):
    """更新指定条件的系统提示词"""
    filename = CONDITION_FILES.get(condition)
    if not filename:
        raise HTTPException(status_code=404, detail="提示词条件不存在")
    path = prompt_manager.get_prompt_path(condition)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(request.content or "", encoding="utf-8")
    prompt_manager.reload(condition)
    return {
        "message": "系统提示词已更新",
        "condition": condition,
        "filename": filename,
        "path": str(path),
    }


@router.get("/checkin/incomplete")
async def get_incomplete_checkin_users(
    admin_id: int = Depends(is_admin),
):
    """获取本周未完成打卡的用户列表（weekly_checkin_count < 阈值）"""
    result = []
    weekly_threshold = _runtime_setting_int("min_weekly_checkins_for_survey", MIN_WEEKLY_CHECKINS_FOR_SURVEY)
    for user in storage.read_users():
        user_id = user.get("id")
        if not isinstance(user_id, int):
            continue
        state = storage.get_user_experiment_state(user_id)
        weekly_count = state.get("weekly_checkin_count", 0)
        if weekly_count < weekly_threshold:
            result.append({
                "id": user_id,
                "username": user.get("username"),
                "weekly_checkin_count": weekly_count,
                "required": weekly_threshold,
            })
    return {
        "users": result,
        "threshold": weekly_threshold,
        "total": len(result),
    }

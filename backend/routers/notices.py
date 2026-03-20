"""
通知系统路由 - 管理员发布通知，用户收到后必须确认
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)

from routers.user import get_current_user
from routers.admin import is_admin
from storage import JsonStorage
from services.weekly_survey_service import sync_weekly_survey_records_for_user

router = APIRouter()
storage = JsonStorage()


def _update_weekly_notice_tracking(user_id: int, notice: dict, *, shown_at: Optional[str] = None, read_at: Optional[str] = None):
    if not notice or notice.get("source") != "system_weekly":
        return

    week_key = str(notice.get("week_key") or "").strip()
    if not week_key:
        return

    updates = {}
    if shown_at:
        updates["shown_at"] = shown_at
    if read_at:
        updates["read_at"] = read_at
    if updates:
        storage.upsert_weekly_survey_record(user_id, week_key, updates)

    current_week = get_china_now().strftime("%Y-W%W")
    if shown_at and week_key == current_week:
        storage.update_user_experiment_state(user_id, {"weekly_survey_popup_shown": True})


# ==================== Pydantic Models ====================

class NoticeCreate(BaseModel):
    title: str
    content: str
    enabled: bool = True
    trigger_msg_count: int = 0   # 0=立即对所有人可见，N=用户消息数>=N时触发
    priority: int = 0            # 越大越先显示


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    enabled: Optional[bool] = None
    trigger_msg_count: Optional[int] = None
    priority: Optional[int] = None


# ==================== Admin Endpoints ====================

@router.get("/admin/notices")
async def list_notices(admin_id: int = Depends(is_admin)):
    """获取所有通知（含禁用）"""
    notices = storage.get_notices(enabled_only=False)
    result = []
    for n in notices:
        n_with_stats = dict(n)
        n_with_stats["read_count"] = storage.get_notice_read_count(n["id"])
        result.append(n_with_stats)
    return {"notices": result}


@router.post("/admin/notices")
async def create_notice(body: NoticeCreate, admin_id: int = Depends(is_admin)):
    """创建通知"""
    notice = storage.create_notice(body.model_dump())
    return {"notice": notice}


@router.put("/admin/notices/{notice_id}")
async def update_notice(
    notice_id: int,
    body: NoticeUpdate,
    admin_id: int = Depends(is_admin),
):
    """更新通知"""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    notice = storage.update_notice(notice_id, updates)
    if not notice:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"notice": notice}


@router.delete("/admin/notices/{notice_id}")
async def delete_notice(notice_id: int, admin_id: int = Depends(is_admin)):
    """删除通知及所有用户状态"""
    ok = storage.delete_notice(notice_id)
    if not ok:
        raise HTTPException(status_code=404, detail="通知不存在")
    return {"message": "已删除"}


# ==================== User Endpoints ====================

@router.get("/notices/pending")
async def get_pending_notices(user_id: int = Depends(get_current_user)):
    """获取当前用户待确认的通知（已触发且未读）"""
    sync_weekly_survey_records_for_user(user_id)
    pending = storage.get_pending_notices_for_user(user_id)
    return {"notices": pending}


@router.get("/notices/inbox")
async def get_inbox(user_id: int = Depends(get_current_user)):
    """获取当前用户收件箱（所有已触发通知，含已读状态）"""
    sync_weekly_survey_records_for_user(user_id)
    inbox = storage.get_inbox_notices_for_user(user_id)
    return {"notices": inbox}


@router.post("/notices/{notice_id}/read")
async def mark_notice_read(
    notice_id: int,
    user_id: int = Depends(get_current_user),
):
    """标记通知已读（用户点了"我知道了"）"""
    notice = storage.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="通知不存在")
    now = get_china_now().isoformat()
    state = storage.upsert_user_notice_state(user_id, notice_id, {
        "read_at": now,
        "shown_at": storage.get_user_notice_state(user_id, notice_id) and
                    storage.get_user_notice_state(user_id, notice_id).get("shown_at") or now,
    })
    _update_weekly_notice_tracking(
        user_id,
        notice,
        shown_at=state.get("shown_at"),
        read_at=now,
    )
    return {"state": state}


@router.post("/notices/{notice_id}/shown")
async def mark_notice_shown(
    notice_id: int,
    user_id: int = Depends(get_current_user),
):
    """记录通知已展示给用户（弹窗出现时调用）"""
    notice = storage.get_notice_by_id(notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="通知不存在")
    existing = storage.get_user_notice_state(user_id, notice_id)
    if not existing or not existing.get("shown_at"):
        now = get_china_now().isoformat()
        storage.upsert_user_notice_state(user_id, notice_id, {
            "shown_at": now,
        })
        _update_weekly_notice_tracking(user_id, notice, shown_at=now)
    return {"ok": True}

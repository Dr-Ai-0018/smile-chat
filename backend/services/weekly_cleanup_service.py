"""
每周清理服务

负责：
1. 手动 / 自动执行每周周次重置
2. 记录执行历史，供管理员回看
3. 维护后台自动任务的启停与调度状态
"""
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from storage import JsonStorage


CHINA_TZ = timezone(timedelta(hours=8))
AUTO_SETTING_KEY = "weekly_cleanup_auto_enabled"
AUTO_START_AT_KEY = "weekly_cleanup_auto_start_at"
AUTO_POLL_INTERVAL_SECONDS = 30

storage = JsonStorage()
_execution_lock = threading.RLock()
_scheduler_task: Optional[asyncio.Task] = None
_scheduler_stop_event: Optional[asyncio.Event] = None


def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHINA_TZ)
        return dt.astimezone(CHINA_TZ)
    except Exception:
        return None


def get_current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")


def get_current_cleanup_slot(dt: Optional[datetime] = None) -> datetime:
    target = (dt or get_china_now()).astimezone(CHINA_TZ)
    local_midnight = target.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight - timedelta(days=target.weekday())


def get_next_cleanup_run(dt: Optional[datetime] = None) -> datetime:
    return get_current_cleanup_slot(dt) + timedelta(days=7)


def get_schedule_label() -> str:
    return "UTC+8 每周日晚 24:00（即周一 00:00）"


def prepare_weekly_cleanup_settings_updates(existing_settings: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    if AUTO_SETTING_KEY not in updates:
        return updates

    previous_enabled = bool(existing_settings.get(AUTO_SETTING_KEY, False))
    next_enabled = bool(updates.get(AUTO_SETTING_KEY))

    if next_enabled and not previous_enabled:
        updates[AUTO_START_AT_KEY] = get_next_cleanup_run().isoformat()
    elif not next_enabled:
        updates[AUTO_START_AT_KEY] = None

    return updates


def execute_weekly_cleanup(
    *,
    reset_checkins: bool,
    trigger_type: str,
    admin_id: Optional[int] = None,
    scheduled_for: Optional[str] = None,
    schedule_slot_key: Optional[str] = None,
) -> Dict[str, Any]:
    with _execution_lock:
        now_iso = get_china_now().isoformat()
        try:
            updated_users = storage.reset_weekly_experiment_state(
                reset_checkins=reset_checkins,
                reset_week_key=reset_checkins,
            )
            entry = storage.append_weekly_cleanup_history({
                "trigger_type": trigger_type,
                "reset_checkins": reset_checkins,
                "success": True,
                "message": "每周清理已执行",
                "updated_users": updated_users,
                "current_week_key": get_current_week_key(),
                "scheduled_for": scheduled_for,
                "schedule_slot_key": schedule_slot_key,
                "admin_id": admin_id,
                "executed_at": now_iso,
            })
            return entry
        except Exception as exc:
            storage.append_weekly_cleanup_history({
                "trigger_type": trigger_type,
                "reset_checkins": reset_checkins,
                "success": False,
                "message": "每周清理执行失败",
                "error": str(exc),
                "updated_users": 0,
                "current_week_key": get_current_week_key(),
                "scheduled_for": scheduled_for,
                "schedule_slot_key": schedule_slot_key,
                "admin_id": admin_id,
                "executed_at": now_iso,
            })
            raise


def _has_successful_auto_run_for_slot(slot_key: str) -> bool:
    history = storage.get_weekly_cleanup_history(limit=0)
    return any(
        str(item.get("trigger_type") or "") == "auto"
        and bool(item.get("success"))
        and str(item.get("schedule_slot_key") or "") == slot_key
        for item in history
    )


def maybe_run_auto_weekly_cleanup(now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    target = (now or get_china_now()).astimezone(CHINA_TZ)
    settings = storage.get_settings()
    if not bool(settings.get(AUTO_SETTING_KEY, False)):
        return None

    slot_dt = get_current_cleanup_slot(target)
    start_at = _parse_iso(settings.get(AUTO_START_AT_KEY))
    if start_at and slot_dt < start_at:
        return None

    slot_key = slot_dt.isoformat()
    if _has_successful_auto_run_for_slot(slot_key):
        return None
    if not storage.claim_weekly_cleanup_slot(slot_key):
        return None

    try:
        return execute_weekly_cleanup(
            reset_checkins=True,
            trigger_type="auto",
            scheduled_for=slot_dt.isoformat(),
            schedule_slot_key=slot_key,
        )
    except Exception:
        storage.release_weekly_cleanup_slot_claim(slot_key)
        raise


def get_weekly_cleanup_status(history_limit: int = 20) -> Dict[str, Any]:
    now = get_china_now()
    settings = storage.get_settings()
    enabled = bool(settings.get(AUTO_SETTING_KEY, False))
    start_at = _parse_iso(settings.get(AUTO_START_AT_KEY))
    current_slot = get_current_cleanup_slot(now)
    current_slot_key = current_slot.isoformat()
    current_slot_done = _has_successful_auto_run_for_slot(current_slot_key)

    if enabled:
        if start_at and current_slot < start_at:
            next_run = start_at
        elif not current_slot_done and now >= current_slot:
            next_run = current_slot
        else:
            next_run = current_slot + timedelta(days=7)
    else:
        next_run = None

    history = storage.get_weekly_cleanup_history(limit=history_limit)
    last_run = history[0] if history else None
    last_auto_run = next((item for item in history if item.get("trigger_type") == "auto"), None)

    return {
        "auto_enabled": enabled,
        "auto_start_at": start_at.isoformat() if start_at else None,
        "timezone": "UTC+8",
        "schedule_label": get_schedule_label(),
        "poll_interval_seconds": AUTO_POLL_INTERVAL_SECONDS,
        "runner_active": bool(_scheduler_task and not _scheduler_task.done()),
        "current_week_key": get_current_week_key(),
        "next_run_at": next_run.isoformat() if next_run else None,
        "last_run": last_run,
        "last_auto_run": last_auto_run,
        "history": history,
    }


async def _scheduler_loop() -> None:
    while _scheduler_stop_event and not _scheduler_stop_event.is_set():
        try:
            maybe_run_auto_weekly_cleanup()
        except Exception as exc:
            print(f"[weekly-cleanup-scheduler] 自动每周清理失败: {exc}")

        try:
            await asyncio.wait_for(_scheduler_stop_event.wait(), timeout=AUTO_POLL_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue


def start_weekly_cleanup_scheduler() -> None:
    global _scheduler_task, _scheduler_stop_event
    if _scheduler_task and not _scheduler_task.done():
        return
    _scheduler_stop_event = asyncio.Event()
    _scheduler_task = asyncio.create_task(_scheduler_loop(), name="weekly-cleanup-scheduler")


async def stop_weekly_cleanup_scheduler() -> None:
    global _scheduler_task, _scheduler_stop_event
    if _scheduler_stop_event is not None:
        _scheduler_stop_event.set()
    if _scheduler_task is not None:
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
    _scheduler_task = None
    _scheduler_stop_event = None

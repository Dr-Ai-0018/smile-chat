"""
每周问卷服务

负责：
1. 根据每周打卡次数同步问卷资格
2. 为达标周次创建用户专属问卷通知
3. 维护按周落盘的问卷历史记录，供管理后台与导出使用
"""
from datetime import datetime, timezone, timedelta
import threading
from typing import Dict, List, Optional

from storage import JsonStorage


CHINA_TZ = timezone(timedelta(hours=8))
DEFAULT_MIN_WEEKLY_CHECKINS_FOR_SURVEY = 2

storage = JsonStorage()
_sync_lock = threading.RLock()


def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)


def get_current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")


def is_weekend(dt: Optional[datetime] = None) -> bool:
    target = dt or get_china_now()
    return target.weekday() >= 5


def _runtime_setting_int(key: str, default: int) -> int:
    settings = storage.get_settings()
    try:
        return int(settings.get(key, default))
    except Exception:
        return default


def build_weekly_survey_content(week_key: str, weekly_count: int, survey_url: str) -> tuple[str, str]:
    title = f"{week_key} 周问卷提醒"
    content = f"你在 {week_key} 已完成 {weekly_count} 次打卡，请填写该周问卷。"
    if survey_url:
        content += f"\n\n[点击填写该周问卷]({survey_url})"
    return title, content


def _group_weekly_checkins(user_id: int) -> Dict[str, int]:
    weekly_counts: Dict[str, int] = {}
    for record in storage.get_checkin_records(user_id):
        week_key = str(record.get("week_key") or "").strip()
        if not week_key:
            continue
        weekly_counts[week_key] = weekly_counts.get(week_key, 0) + 1
    return weekly_counts


def sync_weekly_survey_records_for_user(user_id: int) -> List[dict]:
    with _sync_lock:
        settings = storage.get_settings()
        survey_url = str(settings.get("weekly_survey_url", "") or "").strip()
        required = _runtime_setting_int(
            "min_weekly_checkins_for_survey",
            DEFAULT_MIN_WEEKLY_CHECKINS_FOR_SURVEY,
        )
        weekly_counts = _group_weekly_checkins(user_id)
        existing_records = {
            str(item.get("week_key")): item
            for item in storage.get_weekly_survey_records(user_id=user_id, limit=0)
            if item.get("week_key")
        }

        week_keys = sorted(set(weekly_counts.keys()) | set(existing_records.keys()))
        synced: List[dict] = []
        now = get_china_now()
        now_iso = now.isoformat()
        current_week = get_current_week_key()
        weekend_now = is_weekend(now)

        for week_key in week_keys:
            checkin_count = int(weekly_counts.get(week_key, 0) or 0)
            existing = existing_records.get(week_key) or {}
            notice_id = existing.get("notice_id")
            existing_notice = storage.get_notice_by_id(notice_id) if notice_id else None
            if not existing_notice:
                notice_id = None

            eligible_now = checkin_count >= required
            was_qualified = bool(existing.get("eligible")) or bool(existing.get("qualified_at")) or bool(notice_id)
            eligible = was_qualified or eligible_now

            updates = {
                "weekly_checkin_count_snapshot": checkin_count,
                "eligible": eligible,
            }

            # 尚未派发前，允许随着后台设置调整该周待派发快照。
            if not notice_id:
                updates["required_checkins_snapshot"] = required
                updates["survey_url_snapshot"] = survey_url

            if eligible_now and not existing.get("qualified_at"):
                updates["qualified_at"] = now_iso
                updates["qualified_checkin_count_snapshot"] = checkin_count

            # 当前周问卷只允许在周末派发；历史周次允许补发，避免用户错过上周末后永远收不到。
            can_dispatch_notice = eligible and not notice_id and (
                week_key != current_week or weekend_now
            )

            if can_dispatch_notice:
                title, content = build_weekly_survey_content(week_key, checkin_count, survey_url)
                notice = storage.create_notice({
                    "title": title,
                    "content": content,
                    "enabled": True,
                    "trigger_msg_count": 0,
                    "priority": 10,
                    "source": "system_weekly",
                    "user_id": user_id,
                    "week_key": week_key,
                })
                updates.update({
                    "notice_id": notice["id"],
                    "notice_created_at": now_iso,
                    "qualified_at": existing.get("qualified_at") or now_iso,
                    "qualified_checkin_count_snapshot": existing.get("qualified_checkin_count_snapshot") or checkin_count,
                    "notice_title_snapshot": title,
                    "notice_content_snapshot": content,
                })

            record = storage.upsert_weekly_survey_record(
                user_id=user_id,
                week_key=week_key,
                updates=updates,
            )
            synced.append(record)

        return synced


def get_latest_pending_weekly_survey_notice(user_id: int) -> Optional[dict]:
    sync_weekly_survey_records_for_user(user_id)
    pending = [
        item for item in storage.get_pending_notices_for_user(user_id)
        if item.get("source") == "system_weekly"
    ]
    if not pending:
        return None
    pending.sort(key=lambda item: str(item.get("week_key") or item.get("created_at") or ""), reverse=True)
    return pending[0]

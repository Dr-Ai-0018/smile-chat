"""
打卡系统路由
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from routers.user import get_current_user
from storage import JsonStorage
from services.weekly_survey_service import (
    get_latest_pending_weekly_survey_notice,
    sync_weekly_survey_records_for_user,
)

CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)

def get_current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")

# 实验参数默认值（可被 settings.json 覆盖）
MIN_ROUNDS_FOR_CHECKIN = int(os.getenv("MIN_ROUNDS_FOR_CHECKIN", "10"))
CHECKIN_COOLDOWN_HOURS = int(os.getenv("CHECKIN_COOLDOWN_HOURS", "4"))
CHECKIN_PENDING_EXPIRE_HOURS = int(os.getenv("CHECKIN_PENDING_EXPIRE_HOURS", "4"))
MIN_WEEKLY_CHECKINS_FOR_SURVEY = int(os.getenv("MIN_WEEKLY_CHECKINS_FOR_SURVEY", "2"))

DEFAULT_QUESTIONS = [
    "你现在的孤独感如何？",
    "你现在的情绪状态如何？",
    "你现在的压力程度如何？",
    "你现在的满足感如何？",
    "你现在的社交需求如何？",
]

router = APIRouter()
storage = JsonStorage()


class CheckinSubmitRequest(BaseModel):
    answers: List[int]


def _runtime_setting_int(key: str, default: int) -> int:
    settings = storage.get_settings()
    try:
        value = int(settings.get(key, default))
        return value
    except Exception:
        return default


def _parse_iso_with_tz(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=CHINA_TZ)
        return dt
    except Exception:
        return None


def _cleanup_expired_pending_checkin(user_id: int, state: dict) -> dict:
    """
    可打卡但未打卡超时后，自动清理轮次累计。

    规则：
    - 仅当已达到可打卡轮数阈值时才检查
    - 从「可打卡状态下最后一条消息时间」开始计时
    - 超过 4 小时（可配置）后清零 current_round_count
    """
    min_rounds_for_checkin = _runtime_setting_int("min_rounds_for_checkin", MIN_ROUNDS_FOR_CHECKIN)
    pending_expire_hours = _runtime_setting_int("checkin_pending_expire_hours", CHECKIN_PENDING_EXPIRE_HOURS)
    round_count = int(state.get("current_round_count", 0) or 0)
    if round_count < min_rounds_for_checkin:
        return state

    anchor = _parse_iso_with_tz(
        state.get("checkin_eligible_last_message_time")
        or state.get("last_user_message_time")
    )
    if anchor is None:
        return state

    expire_seconds = max(1, pending_expire_hours * 3600)
    elapsed_seconds = (get_china_now() - anchor).total_seconds()
    if elapsed_seconds <= expire_seconds:
        return state

    return storage.update_user_experiment_state(
        user_id,
        {
            "current_round_count": 0,
            "session_start_time": None,
            "checkin_eligible_last_message_time": None,
        },
    )


def _can_checkin(state: dict) -> tuple[bool, int]:
    """返回 (can_checkin, cooldown_remaining_seconds)"""
    min_rounds_for_checkin = _runtime_setting_int("min_rounds_for_checkin", MIN_ROUNDS_FOR_CHECKIN)
    checkin_cooldown_hours = _runtime_setting_int("checkin_cooldown_hours", CHECKIN_COOLDOWN_HOURS)
    round_count = state.get("current_round_count", 0)
    if round_count < min_rounds_for_checkin:
        return False, 0

    last_checkin_str = state.get("last_checkin_at")
    if last_checkin_str:
        try:
            last_checkin = datetime.fromisoformat(last_checkin_str)
            if last_checkin.tzinfo is None:
                last_checkin = last_checkin.replace(tzinfo=CHINA_TZ)
            elapsed = (get_china_now() - last_checkin).total_seconds()
            cooldown_seconds = checkin_cooldown_hours * 3600
            if elapsed < cooldown_seconds:
                return False, int(cooldown_seconds - elapsed)
        except Exception:
            pass

    return True, 0


@router.get("/checkin/status")
async def get_checkin_status(user_id: int = Depends(get_current_user)):
    """获取当前打卡状态"""
    state = storage.get_user_experiment_state(user_id)
    state = _cleanup_expired_pending_checkin(user_id, state)
    can, cooldown = _can_checkin(state)
    sync_weekly_survey_records_for_user(user_id)

    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)

    return {
        "round_count": state.get("current_round_count", 0),
        "can_checkin": can,
        "cooldown_remaining_seconds": cooldown,
        "weekly_checkin_count": state.get("weekly_checkin_count", 0),
        "questions": questions,
        "min_rounds_for_checkin": _runtime_setting_int("min_rounds_for_checkin", MIN_ROUNDS_FOR_CHECKIN),
        "checkin_cooldown_hours": _runtime_setting_int("checkin_cooldown_hours", CHECKIN_COOLDOWN_HOURS),
    }


@router.post("/checkin/submit")
async def submit_checkin(
    body: CheckinSubmitRequest,
    user_id: int = Depends(get_current_user),
):
    """提交打卡"""
    state = storage.get_user_experiment_state(user_id)
    state = _cleanup_expired_pending_checkin(user_id, state)
    can, _ = _can_checkin(state)
    if not can:
        raise HTTPException(status_code=400, detail="当前不满足打卡条件")

    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=400, detail=f"答案数量应为 {len(questions)}")

    for v in body.answers:
        if not (1 <= v <= 7):
            raise HTTPException(status_code=400, detail="每题分值应在 1~7 之间")

    now = get_china_now()
    week_key = get_current_week_key()
    answers = {f"q{i}": v for i, v in enumerate(body.answers)}
    round_count = state.get("current_round_count", 0)

    record = storage.create_checkin_record(
        user_id=user_id,
        answers=answers,
        round_count=round_count,
        week_key=week_key,
        questions_snapshot=questions,
    )

    state = storage.update_user_experiment_state(user_id, {
        "current_round_count": 0,
        "last_checkin_at": now.isoformat(),
        "weekly_checkin_count": state.get("weekly_checkin_count", 0) + 1,
        "session_start_time": None,
        "checkin_eligible_last_message_time": None,
    })
    weekly_records = sync_weekly_survey_records_for_user(user_id)
    current_week_record = next((item for item in weekly_records if item.get("week_key") == week_key), None)

    return {
        "ok": True,
        "record_id": record["id"],
        "weekly_checkin_count": state.get("weekly_checkin_count", 0),
        "weekly_survey_status": current_week_record,
    }


@router.get("/checkin/weekend_survey_check")
async def weekend_survey_check(user_id: int = Depends(get_current_user)):
    """
    同步并检查用户是否存在待展示的周问卷提醒。

    兼容旧接口名称。当前周问卷仅允许在周末、且达到本周打卡阈值后派发；
    对历史周次则允许补发，避免用户错过上周末后无法再收到提醒。
    """
    notice = get_latest_pending_weekly_survey_notice(user_id)
    if not notice:
        return {
            "should_popup": False,
            "notice_id": None,
            "survey_url": None,
            "notice_content": None,
            "week_key": None,
        }

    weekly_record = next(
        (
            item for item in storage.get_weekly_survey_records(user_id=user_id, limit=0)
            if item.get("notice_id") == notice.get("id")
        ),
        None,
    )
    survey_url = ""
    if weekly_record:
        survey_url = str(weekly_record.get("survey_url_snapshot") or "").strip()

    return {
        "should_popup": True,
        "notice_id": notice["id"],
        "survey_url": survey_url,
        "notice_content": notice.get("content"),
        "week_key": notice.get("week_key"),
        "weekly_record": weekly_record,
    }


@router.get("/checkin/questions")
async def get_questions(user_id: int = Depends(get_current_user)):
    """获取打卡题目列表"""
    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)
    return {"questions": questions}

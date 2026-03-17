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

CHINA_TZ = timezone(timedelta(hours=8))

def get_china_now() -> datetime:
    return datetime.now(CHINA_TZ)

def get_current_week_key() -> str:
    return get_china_now().strftime("%Y-W%W")

# 实验参数
MIN_ROUNDS_FOR_CHECKIN = int(os.getenv("MIN_ROUNDS_FOR_CHECKIN", "10"))
CHECKIN_COOLDOWN_HOURS = int(os.getenv("CHECKIN_COOLDOWN_HOURS", "4"))
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


def _can_checkin(state: dict) -> tuple[bool, int]:
    """返回 (can_checkin, cooldown_remaining_seconds)"""
    round_count = state.get("current_round_count", 0)
    if round_count < MIN_ROUNDS_FOR_CHECKIN:
        return False, 0

    last_checkin_str = state.get("last_checkin_at")
    if last_checkin_str:
        try:
            last_checkin = datetime.fromisoformat(last_checkin_str)
            if last_checkin.tzinfo is None:
                last_checkin = last_checkin.replace(tzinfo=CHINA_TZ)
            elapsed = (get_china_now() - last_checkin).total_seconds()
            cooldown_seconds = CHECKIN_COOLDOWN_HOURS * 3600
            if elapsed < cooldown_seconds:
                return False, int(cooldown_seconds - elapsed)
        except Exception:
            pass

    return True, 0


@router.get("/checkin/status")
async def get_checkin_status(user_id: int = Depends(get_current_user)):
    """获取当前打卡状态"""
    state = storage.get_user_experiment_state(user_id)
    can, cooldown = _can_checkin(state)

    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)

    return {
        "round_count": state.get("current_round_count", 0),
        "can_checkin": can,
        "cooldown_remaining_seconds": cooldown,
        "weekly_checkin_count": state.get("weekly_checkin_count", 0),
        "questions": questions,
        "min_rounds_for_checkin": MIN_ROUNDS_FOR_CHECKIN,
    }


@router.post("/checkin/submit")
async def submit_checkin(
    body: CheckinSubmitRequest,
    user_id: int = Depends(get_current_user),
):
    """提交打卡"""
    state = storage.get_user_experiment_state(user_id)
    can, _ = _can_checkin(state)
    if not can:
        raise HTTPException(status_code=400, detail="当前不满足打卡条件")

    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)
    if len(body.answers) != len(questions):
        raise HTTPException(status_code=400, detail=f"答案数量应为 {len(questions)}")

    for v in body.answers:
        if not (1 <= v <= 10):
            raise HTTPException(status_code=400, detail="每题分值应在 1~10 之间")

    now = get_china_now()
    week_key = get_current_week_key()
    answers = {f"q{i}": v for i, v in enumerate(body.answers)}
    round_count = state.get("current_round_count", 0)

    record = storage.create_checkin_record(
        user_id=user_id,
        answers=answers,
        round_count=round_count,
        week_key=week_key,
    )

    storage.update_user_experiment_state(user_id, {
        "current_round_count": 0,
        "last_checkin_at": now.isoformat(),
        "weekly_checkin_count": state.get("weekly_checkin_count", 0) + 1,
        "session_start_time": None,
    })

    return {"ok": True, "record_id": record["id"]}


@router.get("/checkin/weekend_survey_check")
async def weekend_survey_check(user_id: int = Depends(get_current_user)):
    """用户上线时调用，检查是否需要弹出周末问卷"""
    now = get_china_now()
    weekday = now.weekday()  # 0=周一 ... 5=周六 6=周日
    is_weekend = weekday in (5, 6)

    if not is_weekend:
        return {"should_popup": False, "notice_id": None, "survey_url": None}

    state = storage.get_user_experiment_state(user_id)
    weekly_count = state.get("weekly_checkin_count", 0)
    already_shown = state.get("weekly_survey_popup_shown", False)

    if weekly_count < MIN_WEEKLY_CHECKINS_FOR_SURVEY or already_shown:
        return {"should_popup": False, "notice_id": None, "survey_url": None}

    # 满足条件：写入用户专属 notice（收件箱可回看），标记本周已弹
    settings = storage.get_settings()
    survey_url = settings.get("weekly_survey_url", "")

    content = f"本周你已完成 {weekly_count} 次打卡，请填写本周问卷。"
    if survey_url:
        content += f"\n\n[点击填写问卷]({survey_url})"

    notice = storage.create_notice({
        "title": "本周问卷提醒",
        "content": content,
        "enabled": True,
        "trigger_msg_count": 0,
        "priority": 10,
        "source": "system_weekly",
        "user_id": user_id,  # 用户专属，不泄漏给其他人
    })
    # 标记已展示（首次自动弹）
    storage.upsert_user_notice_state(user_id, notice["id"], {
        "shown_at": now.isoformat(),
    })
    storage.update_user_experiment_state(user_id, {"weekly_survey_popup_shown": True})

    return {
        "should_popup": True,
        "notice_id": notice["id"],
        "survey_url": survey_url,
        "notice_content": content,
    }


@router.get("/checkin/questions")
async def get_questions(user_id: int = Depends(get_current_user)):
    """获取打卡题目列表"""
    settings = storage.get_settings()
    questions = settings.get("checkin_questions", DEFAULT_QUESTIONS)
    return {"questions": questions}

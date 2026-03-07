"""Study plan service: daily recalculation of study mode for a user."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from supabase import Client

from app.core.study_plan.planner import StudyMode, determine_mode, new_cards_limit


@dataclass
class StudyPlan:
    mode: StudyMode
    days_until_exam: int
    new_cards_limit: int
    exam_date: date | None


def get_study_plan(sb: Client, user_id: str) -> StudyPlan:
    """Fetch the user's exam_date, determine the current study mode, and return a StudyPlan.

    Also persists the recalculated study_plan_type back to the users table so
    other parts of the system can read it without recomputing.
    """
    resp = (
        sb.table("users")
        .select("exam_date, daily_goal_minutes")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    user_row = resp.data or {}
    exam_date_raw: str | None = user_row.get("exam_date")

    if exam_date_raw is None:
        # No exam date set yet — default to relaxed
        return StudyPlan(
            mode="relaxed",
            days_until_exam=9999,
            new_cards_limit=new_cards_limit("relaxed"),
            exam_date=None,
        )

    exam_date = _parse_date(exam_date_raw)
    today = datetime.now(timezone.utc).date()
    days_remaining = max(0, (exam_date - today).days)
    mode = determine_mode(days_remaining)

    # Persist updated study_plan_type
    sb.table("users").update({"study_plan_type": mode}).eq("id", user_id).execute()

    return StudyPlan(
        mode=mode,
        days_until_exam=days_remaining,
        new_cards_limit=new_cards_limit(mode),
        exam_date=exam_date,
    )


def _parse_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    # ISO format: "YYYY-MM-DD" or full datetime string
    return date.fromisoformat(value[:10])

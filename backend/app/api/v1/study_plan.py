"""GET /api/v1/study-plan endpoint."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from supabase import Client

from app.api.deps import CurrentUser
from app.db.supabase import get_supabase_client
from app.services.study_plan_service import StudyPlan, get_study_plan

router = APIRouter()


class StudyPlanResponse(BaseModel):
    mode: str
    days_until_exam: int
    new_cards_limit: int
    exam_date: date | None


@router.get("/study-plan", response_model=StudyPlanResponse)
def read_study_plan(
    current_user: CurrentUser,
    sb: Client = Depends(get_supabase_client),
) -> Any:
    """Return the authenticated user's current adaptive study plan."""
    plan: StudyPlan = get_study_plan(sb, current_user["user_id"])
    return StudyPlanResponse(
        mode=plan.mode,
        days_until_exam=plan.days_until_exam,
        new_cards_limit=plan.new_cards_limit,
        exam_date=plan.exam_date,
    )

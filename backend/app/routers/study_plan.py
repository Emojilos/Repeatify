"""Study Plan API: generate, retrieve, recalculate, and get today's tasks."""

from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.supabase_client import get_supabase_client
from app.models.study_plan import (
    DailyTask,
    DailyTasksResponse,
    StudyPlanGenerateRequest,
    StudyPlanResponse,
)
from app.services.study_plan_service import (
    generate_plan,
    get_current_plan,
)

router = APIRouter(prefix="/api/study-plan", tags=["study-plan"])


@router.post("/generate", response_model=StudyPlanResponse, status_code=201)
@limiter.limit(settings.STUDY_PLAN_GENERATE_RATE_LIMIT)
async def generate_study_plan(
    request: Request,
    body: StudyPlanGenerateRequest,
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Generate a personalised study plan based on diagnostic results and goals."""
    client = get_supabase_client()

    plan = generate_plan(
        client,
        user_id=user["id"],
        target_score=body.target_score,
        exam_date_str=body.exam_date,
        hours_per_day=body.hours_per_day,
    )

    return StudyPlanResponse(
        id=plan["id"],
        user_id=plan["user_id"],
        target_score=plan["target_score"],
        exam_date=plan["exam_date"],
        hours_per_day=plan["hours_per_day"],
        plan_data=plan["plan_data"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        is_active=plan["is_active"],
    )


@router.get("/current", response_model=StudyPlanResponse)
async def get_current_study_plan(
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Return the user's active study plan."""
    client = get_supabase_client()

    plan = get_current_plan(client, user["id"])
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active study plan found. Generate one first.",
        )

    return StudyPlanResponse(
        id=plan["id"],
        user_id=plan["user_id"],
        target_score=plan["target_score"],
        exam_date=plan["exam_date"],
        hours_per_day=plan["hours_per_day"],
        plan_data=plan.get("plan_data"),
        generated_at=plan.get("generated_at", ""),
        is_active=plan["is_active"],
    )


@router.put("/recalculate", response_model=StudyPlanResponse)
async def recalculate_study_plan(
    body: StudyPlanGenerateRequest,
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Recalculate the study plan with updated parameters.

    Deactivates the existing plan and creates a new one.
    """
    client = get_supabase_client()

    # Verify a plan exists before recalculating
    existing = get_current_plan(client, user["id"])
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active study plan to recalculate. Generate one first.",
        )

    plan = generate_plan(
        client,
        user_id=user["id"],
        target_score=body.target_score,
        exam_date_str=body.exam_date,
        hours_per_day=body.hours_per_day,
    )

    return StudyPlanResponse(
        id=plan["id"],
        user_id=plan["user_id"],
        target_score=plan["target_score"],
        exam_date=plan["exam_date"],
        hours_per_day=plan["hours_per_day"],
        plan_data=plan["plan_data"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        is_active=plan["is_active"],
    )


@router.get("/today", response_model=DailyTasksResponse)
async def get_today_tasks(
    user: dict = Depends(get_current_user),
) -> DailyTasksResponse:
    """Return today's tasks: FSRS cards due + next topic from the plan."""
    client = get_supabase_client()

    # 1) Count due FSRS cards
    now = datetime.now(timezone.utc).isoformat()
    due_result = (
        client.table("fsrs_cards")
        .select("id")
        .eq("user_id", user["id"])
        .lte("due", now)
        .neq("state", "new")
        .execute()
    )
    review_cards_due = len(due_result.data or [])

    # 2) Get today's new material from the active plan
    new_material: list[DailyTask] = []
    total_estimated_minutes = review_cards_due * 2  # ~2 min per review card

    plan = get_current_plan(client, user["id"])
    if plan and plan.get("plan_data"):
        plan_data = plan["plan_data"]
        today_str = date.today().isoformat()

        # Find today's entry in the plan weeks
        for week in plan_data.get("weeks", []):
            for day in week.get("days", []):
                if day.get("date") == today_str:
                    for study_item in day.get("study", []):
                        task_number = study_item.get("task_number")
                        minutes = study_item.get("minutes", 0)

                        # Look up topic title for this task_number
                        title = f"Задание {task_number}"
                        topic_result = (
                            client.table("topics")
                            .select("title")
                            .eq("task_number", task_number)
                            .execute()
                        )
                        if topic_result.data:
                            title = topic_result.data[0].get("title", title)

                        new_material.append(DailyTask(
                            task_type="study",
                            task_number=task_number,
                            title=title,
                            estimated_minutes=minutes,
                        ))
                        total_estimated_minutes += minutes

                    # Also add review minutes from plan
                    total_estimated_minutes += day.get("review_minutes", 0)
                    break
            else:
                continue
            break

    return DailyTasksResponse(
        review_cards_due=review_cards_due,
        new_material=new_material,
        total_estimated_minutes=total_estimated_minutes,
    )

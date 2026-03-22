"""Study Plan API: generate knowledge map, run task assessments."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.supabase_client import get_supabase_client
from app.models.study_plan import (
    AssessmentResultResponse,
    AssessmentStartResponse,
    AssessmentSubmitRequest,
    StudyPlanGenerateRequest,
    StudyPlanResponse,
)
from app.services.study_plan_service import (
    generate_plan,
    get_current_plan,
    start_assessment,
    submit_assessment,
)

router = APIRouter(prefix="/api/study-plan", tags=["study-plan"])


@router.post("/generate", response_model=StudyPlanResponse, status_code=201)
@limiter.limit(settings.STUDY_PLAN_GENERATE_RATE_LIMIT)
async def generate_study_plan(
    request: Request,
    body: StudyPlanGenerateRequest,
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Generate a knowledge-map study plan based on target score and assessments."""
    client = get_supabase_client()

    plan = generate_plan(
        client,
        user_id=user["id"],
        target_score=body.target_score,
    )

    return StudyPlanResponse(
        id=plan["id"],
        user_id=plan["user_id"],
        target_score=plan["target_score"],
        plan_data=plan["plan_data"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        is_active=plan["is_active"],
    )


@router.get("/current", response_model=StudyPlanResponse)
async def get_current_study_plan(
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Return the user's active study plan (knowledge map)."""
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
        plan_data=plan.get("plan_data"),
        generated_at=plan.get("generated_at", ""),
        is_active=plan["is_active"],
    )


@router.put("/recalculate", response_model=StudyPlanResponse)
async def recalculate_study_plan(
    body: StudyPlanGenerateRequest,
    user: dict = Depends(get_current_user),
) -> StudyPlanResponse:
    """Recalculate the study plan with updated target score."""
    client = get_supabase_client()

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
    )

    return StudyPlanResponse(
        id=plan["id"],
        user_id=plan["user_id"],
        target_score=plan["target_score"],
        plan_data=plan["plan_data"],
        generated_at=datetime.now(timezone.utc).isoformat(),
        is_active=plan["is_active"],
    )


@router.post(
    "/assess/{task_number}",
    response_model=AssessmentStartResponse,
)
async def start_task_assessment(
    task_number: int,
    user: dict = Depends(get_current_user),
) -> AssessmentStartResponse:
    """Start an assessment test for a specific task. Returns 10 problems."""
    if task_number < 1 or task_number > 19:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_number must be between 1 and 19",
        )

    client = get_supabase_client()
    problems = start_assessment(client, user["id"], task_number)

    if not problems:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No problems found for task {task_number}",
        )

    return AssessmentStartResponse(
        task_number=task_number,
        problems=problems,
    )


@router.post(
    "/assess/{task_number}/submit",
    response_model=AssessmentResultResponse,
)
async def submit_task_assessment(
    task_number: int,
    body: AssessmentSubmitRequest,
    user: dict = Depends(get_current_user),
) -> AssessmentResultResponse:
    """Submit assessment answers and get results. Updates mastery level."""
    if task_number < 1 or task_number > 19:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="task_number must be between 1 and 19",
        )

    if not body.answers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="answers list cannot be empty",
        )

    client = get_supabase_client()

    result = submit_assessment(
        client,
        user_id=user["id"],
        task_number=task_number,
        answers=[a.model_dump() for a in body.answers],
    )

    # Regenerate plan to reflect updated mastery
    plan = get_current_plan(client, user["id"])
    if plan:
        generate_plan(
            client,
            user_id=user["id"],
            target_score=plan["target_score"],
        )

    return AssessmentResultResponse(
        task_number=result["task_number"],
        correct_count=result["correct_count"],
        total_count=result["total_count"],
        status=result["status"],
        details=result["details"],
    )

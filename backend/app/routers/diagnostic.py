"""Diagnostic test endpoints: start test, submit answers, get results."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.supabase_client import get_supabase_client
from app.models.diagnostic import (
    DiagnosticProblem,
    DiagnosticResultItem,
    DiagnosticResultResponse,
    DiagnosticStartResponse,
    DiagnosticSubmitRequest,
)
from app.services.diagnostic_service import (
    grade_and_persist,
    has_existing_diagnostic,
    initialize_fsrs_from_diagnostic,
    select_problems_for_diagnostic,
)

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])


@router.api_route("/start", methods=["GET", "POST"], response_model=DiagnosticStartResponse)
async def start_diagnostic(
    user: dict = Depends(get_current_user),
) -> DiagnosticStartResponse:
    """Start a diagnostic test: returns 19 problems (one per task_number).

    If user already has diagnostic results, returns 409 Conflict.
    """
    client = get_supabase_client()

    if has_existing_diagnostic(client, user["id"]):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Diagnostic test already completed."
                " Use POST /api/diagnostic/retake to start a new one."
            ),
        )

    problems = select_problems_for_diagnostic(client, user["id"])

    return DiagnosticStartResponse(
        problems=[
            DiagnosticProblem(
                problem_id=p["problem_id"],
                task_number=p["task_number"],
                problem_text=p["problem_text"],
                problem_images=p.get("problem_images"),
            )
            for p in problems
        ],
        total=len(problems),
    )


@router.post("/submit", response_model=DiagnosticResultResponse)
@limiter.limit(settings.DIAGNOSTIC_SUBMIT_RATE_LIMIT)
async def submit_diagnostic(
    request: Request,
    body: DiagnosticSubmitRequest,
    user: dict = Depends(get_current_user),
) -> DiagnosticResultResponse:
    """Submit diagnostic test answers (19 answers, one per task_number).

    Part 1 (tasks 1-12): auto-checked against correct_answer.
    Part 2 (tasks 13-19): self_assessment stored as-is.
    """
    client = get_supabase_client()

    # Validate all 19 task_numbers are present and unique
    task_numbers = [a.task_number for a in body.answers]
    if len(set(task_numbers)) != 19:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="All 19 task_numbers must be unique.",
        )

    answers_dicts = [
        {
            "task_number": a.task_number,
            "answer": a.answer,
            "self_assessment": a.self_assessment,
            "time_spent_seconds": a.time_spent_seconds,
        }
        for a in body.answers
    ]

    results = grade_and_persist(client, user["id"], answers_dicts)

    # Initialize FSRS cards from diagnostic results (PRD 5.3)
    initialize_fsrs_from_diagnostic(client, user["id"], results)

    total_correct = sum(1 for r in results if r["is_correct"] is True)
    total_answered = sum(
        1 for r in results
        if r["is_correct"] is not None or r["self_assessment"] is not None
    )

    return DiagnosticResultResponse(
        results=[DiagnosticResultItem(**r) for r in results],
        total_correct=total_correct,
        total_answered=total_answered,
    )


@router.post("/retake", response_model=DiagnosticStartResponse)
async def retake_diagnostic(
    user: dict = Depends(get_current_user),
) -> DiagnosticStartResponse:
    """Start a new diagnostic test (allows retake even if previous exists)."""
    client = get_supabase_client()

    problems = select_problems_for_diagnostic(client, user["id"])

    return DiagnosticStartResponse(
        problems=[
            DiagnosticProblem(
                problem_id=p["problem_id"],
                task_number=p["task_number"],
                problem_text=p["problem_text"],
                problem_images=p.get("problem_images"),
            )
            for p in problems
        ],
        total=len(problems),
    )


@router.get("/results", response_model=DiagnosticResultResponse)
async def get_diagnostic_results(
    user: dict = Depends(get_current_user),
) -> DiagnosticResultResponse:
    """Get the user's latest diagnostic results."""
    client = get_supabase_client()

    result = (
        client.table("diagnostic_results")
        .select("task_number,is_correct,self_assessment,time_spent_seconds")
        .eq("user_id", user["id"])
        .order("task_number")
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No diagnostic results found. Start a diagnostic test first.",
        )

    results = result.data
    total_correct = sum(1 for r in results if r["is_correct"] is True)
    total_answered = sum(
        1 for r in results
        if r["is_correct"] is not None or r.get("self_assessment") is not None
    )

    return DiagnosticResultResponse(
        results=[DiagnosticResultItem(**r) for r in results],
        total_correct=total_correct,
        total_answered=total_answered,
    )

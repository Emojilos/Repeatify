import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.problems import (
    AttemptRequest,
    AttemptResponse,
    Difficulty,
    ProblemDetail,
    ProblemListItem,
    ProblemListResponse,
)
from app.services.fsrs_service import create_card as fsrs_create_card
from app.services.fsrs_service import review_card as fsrs_review_card
from app.services.streak_service import record_activity
from app.services.xp_service import award_xp, calculate_problem_xp

router = APIRouter(prefix="/api/problems", tags=["problems"])


def _determine_fsrs_rating(is_correct: bool, time_spent_seconds: int) -> int:
    """Determine FSRS rating from attempt result.

    correct + fast (<60s) → Easy (4)
    correct → Good (3)
    incorrect → Again (1)
    """
    if not is_correct:
        return 1
    if time_spent_seconds < 60:
        return 4
    return 3


def _ensure_fsrs_card(
    client,
    user_id: str,
    problem_id: str,
    is_correct: bool,
    time_spent_seconds: int,
) -> None:
    """Create an FSRS card on first attempt, or review existing card."""
    existing = (
        client.table("fsrs_cards")
        .select("id")
        .eq("user_id", user_id)
        .eq("problem_id", problem_id)
        .execute()
    )

    rating = _determine_fsrs_rating(is_correct, time_spent_seconds)

    if existing.data:
        # Review existing card
        fsrs_review_card(client, existing.data[0]["id"], rating, user_id)
    else:
        # Create new card and immediately review it
        card = fsrs_create_card(
            client, user_id, card_type="problem", problem_id=problem_id,
        )
        fsrs_review_card(client, card["id"], rating, user_id)


def _row_to_list_item(row: dict, max_points: int | None = None) -> ProblemListItem:
    return ProblemListItem(
        id=row["id"],
        topic_id=row["topic_id"],
        task_number=row["task_number"],
        difficulty=row["difficulty"],
        problem_text=row["problem_text"],
        problem_images=row.get("problem_images"),
        hints=row.get("hints"),
        source=row.get("source"),
        max_points=max_points,
    )


def _row_to_detail(row: dict) -> ProblemDetail:
    return ProblemDetail(
        id=row["id"],
        topic_id=row["topic_id"],
        task_number=row["task_number"],
        difficulty=row["difficulty"],
        problem_text=row["problem_text"],
        problem_images=row.get("problem_images"),
        hints=row.get("hints"),
        source=row.get("source"),
    )


@router.get("", response_model=ProblemListResponse)
async def list_problems(
    topic_id: str | None = Query(None),
    difficulty: Difficulty | None = Query(None),
    task_number: int | None = Query(None, ge=1, le=19),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: dict = Depends(get_current_user),
) -> ProblemListResponse:
    """List problems with optional filters and pagination."""
    client = get_supabase_client()

    query = client.table("problems").select("*", count="exact")

    if topic_id is not None:
        query = query.eq("topic_id", topic_id)
    if difficulty is not None:
        query = query.eq("difficulty", difficulty.value)
    if task_number is not None:
        query = query.eq("task_number", task_number)

    offset = (page - 1) * page_size
    query = query.order("task_number").range(offset, offset + page_size - 1)

    result = query.execute()
    problems = result.data or []
    total = result.count if result.count is not None else len(problems)

    # Get max_points from topics for enrichment
    topic_ids = list({p["topic_id"] for p in problems})
    points_map: dict[str, int] = {}
    if topic_ids:
        topics_result = (
            client.table("topics")
            .select("id,max_points")
            .in_("id", topic_ids)
            .execute()
        )
        for t in topics_result.data or []:
            points_map[t["id"]] = t["max_points"]

    items = [
        _row_to_list_item(p, points_map.get(p["topic_id"]))
        for p in problems
    ]

    return ProblemListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{problem_id}", response_model=ProblemDetail)
async def get_problem(
    problem_id: str,
    _user: dict = Depends(get_current_user),
) -> ProblemDetail:
    """Return a single problem WITHOUT correct_answer."""
    client = get_supabase_client()

    result = (
        client.table("problems")
        .select("*")
        .eq("id", problem_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    return _row_to_detail(result.data[0])


@router.get("/{problem_id}/solution")
async def get_solution(
    problem_id: str,
    _user: dict = Depends(get_current_user),
) -> dict:
    """Return solution_markdown for a problem (used by Part 2 flow)."""
    client = get_supabase_client()
    result = (
        client.table("problems")
        .select("solution_markdown")
        .eq("id", problem_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )
    return {"solution_markdown": result.data[0].get("solution_markdown")}


@router.post("/{problem_id}/attempt", response_model=AttemptResponse)
async def submit_attempt(
    problem_id: str,
    body: AttemptRequest,
    user: dict = Depends(get_current_user),
) -> AttemptResponse:
    """Submit an answer attempt. Returns correctness and XP."""
    client = get_supabase_client()

    # Fetch problem with correct_answer
    result = (
        client.table("problems")
        .select("*")
        .eq("id", problem_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    problem = result.data[0]
    correct_answer = (problem.get("correct_answer") or "").strip()
    user_answer = body.answer.strip()

    # Check correctness: exact match (case-insensitive) or within tolerance
    tolerance = problem.get("answer_tolerance") or 0.0
    is_correct = False
    if correct_answer:
        if user_answer.lower() == correct_answer.lower():
            is_correct = True
        elif tolerance > 0:
            try:
                diff = abs(float(user_answer) - float(correct_answer))
                is_correct = diff <= tolerance
            except ValueError:
                pass

    # Calculate XP
    xp_earned = calculate_problem_xp(
        is_correct, problem["task_number"], body.self_assessment.value,
    )

    # Record attempt
    attempt_id = str(uuid.uuid4())
    client.table("user_problem_attempts").insert({
        "id": attempt_id,
        "user_id": user["id"],
        "problem_id": problem_id,
        "user_answer": user_answer,
        "is_correct": is_correct,
        "self_assessment": body.self_assessment.value,
        "time_spent_seconds": body.time_spent_seconds,
    }).execute()

    # Award XP and recalculate level
    _, new_level_reached = award_xp(client, user["id"], xp_earned)

    # FSRS: create card on first attempt, or review existing card
    _ensure_fsrs_card(
        client, user["id"], problem_id, is_correct, body.time_spent_seconds,
    )

    # Record daily activity and update streak
    record_activity(
        client,
        user["id"],
        problems_solved=1,
        xp_earned=xp_earned,
    )

    return AttemptResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        solution_markdown=problem.get("solution_markdown"),
        xp_earned=xp_earned,
        new_level_reached=new_level_reached,
        attempt_id=attempt_id,
    )

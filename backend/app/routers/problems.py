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

router = APIRouter(prefix="/api/problems", tags=["problems"])

# XP rewards
_XP_PART1_CORRECT = 10  # tasks 1-12
_XP_PART2_CORRECT = 25  # tasks 13-19 (only for good/easy)


def _is_part2(task_number: int) -> bool:
    return task_number >= 13


def _calculate_xp(
    is_correct: bool,
    task_number: int,
    self_assessment: str,
) -> int:
    if not is_correct:
        return 0
    if _is_part2(task_number):
        if self_assessment in ("good", "easy"):
            return _XP_PART2_CORRECT
        return 0
    return _XP_PART1_CORRECT


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
        .maybe_single()
        .execute()
    )
    if result.data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    return _row_to_detail(result.data)


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
        .maybe_single()
        .execute()
    )
    if result.data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Problem not found",
        )

    problem = result.data
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
    xp_earned = _calculate_xp(
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

    # Award XP to user
    if xp_earned > 0:
        user_result = (
            client.table("users")
            .select("current_xp")
            .eq("id", user["id"])
            .maybe_single()
            .execute()
        )
        if user_result.data:
            new_xp = (user_result.data.get("current_xp") or 0) + xp_earned
            (
                client.table("users")
                .update({"current_xp": new_xp})
                .eq("id", user["id"])
                .execute()
            )

    return AttemptResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        solution_markdown=problem.get("solution_markdown"),
        xp_earned=xp_earned,
        attempt_id=attempt_id,
    )

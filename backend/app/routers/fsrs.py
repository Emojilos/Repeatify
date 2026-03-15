"""FSRS session endpoints: session generation + review.

Coexists with the old /api/srs/ endpoints for backward compatibility.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.fsrs_card import (
    FSRSCardResponse,
    FSRSReviewRequest,
    FSRSReviewResponse,
    FSRSSessionResponse,
)
from app.services.fsrs_service import (
    get_retrievability,
    get_session,
    review_card,
)
from app.services.streak_service import record_activity
from app.services.xp_service import award_xp, calculate_problem_xp

router = APIRouter(prefix="/api/fsrs", tags=["fsrs"])


def _rating_to_assessment(rating: int) -> str:
    """Map FSRS rating (1-4) to self_assessment string for XP calculation."""
    return {1: "again", 2: "hard", 3: "good", 4: "easy"}[rating]


@router.get("/session", response_model=FSRSSessionResponse)
async def get_fsrs_session(
    max_cards: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
) -> FSRSSessionResponse:
    """Build an FSRS review session from due cards.

    Cards are sorted by retrievability (lowest first) and interleaved
    so no more than 2 consecutive cards share the same task_number.
    """
    client = get_supabase_client()

    # Fetch user's exam_date for retention tuning
    exam_date = _get_exam_date(client, user["id"])

    cards = get_session(client, user["id"], max_cards=max_cards, exam_date=exam_date)

    response_cards = [
        FSRSCardResponse(
            id=c["id"],
            user_id=c["user_id"],
            problem_id=c.get("problem_id"),
            prototype_id=c.get("prototype_id"),
            card_type=c.get("card_type", "problem"),
            difficulty=c.get("difficulty", 0),
            stability=c.get("stability", 0),
            due=c.get("due", ""),
            last_review=c.get("last_review"),
            reps=c.get("reps", 0),
            lapses=c.get("lapses", 0),
            state=c.get("state", "new"),
            scheduled_days=c.get("scheduled_days"),
            elapsed_days=c.get("elapsed_days"),
            created_at=c.get("created_at"),
            problem_text=c.get("problem_text"),
            problem_images=c.get("problem_images"),
            hints=c.get("hints"),
            topic_title=c.get("topic_title"),
            task_number=c.get("task_number"),
            retrievability=c.get("retrievability"),
        )
        for c in cards
    ]

    # Total due = all due cards, not just the ones in the session
    now = datetime.now(timezone.utc).isoformat()
    total_result = (
        client.table("fsrs_cards")
        .select("id")
        .eq("user_id", user["id"])
        .lte("due", now)
        .neq("state", "new")
        .execute()
    )
    total_due = len(total_result.data or [])

    return FSRSSessionResponse(cards=response_cards, total_due=total_due)


@router.post("/review", response_model=FSRSReviewResponse)
async def submit_fsrs_review(
    body: FSRSReviewRequest,
    user: dict = Depends(get_current_user),
) -> FSRSReviewResponse:
    """Record an FSRS review result and update the card schedule."""
    client = get_supabase_client()

    # Fetch user's exam_date
    exam_date = _get_exam_date(client, user["id"])

    # Review the card via FSRS service
    try:
        updated_row = review_card(
            client,
            card_id=body.card_id,
            rating=body.rating,
            user_id=user["id"],
            exam_date=exam_date,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="FSRS card not found",
        )

    # Fetch problem for answer checking + XP
    problem_id = updated_row.get("problem_id")
    is_correct = False
    correct_answer: str | None = None
    solution_markdown: str | None = None
    task_number = 0

    if problem_id:
        prob_result = (
            client.table("problems")
            .select("correct_answer,solution_markdown,task_number,topic_id")
            .eq("id", problem_id)
            .execute()
        )
        if prob_result.data:
            prob = prob_result.data[0]
            correct_answer = (prob.get("correct_answer") or "").strip()
            solution_markdown = prob.get("solution_markdown")
            task_number = prob.get("task_number", 0)
            topic_id = prob.get("topic_id")

            # Check answer
            user_answer = body.answer.strip()
            if user_answer and correct_answer:
                is_correct = user_answer.lower() == correct_answer.lower()

            # Record attempt
            client.table("user_problem_attempts").insert({
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "problem_id": problem_id,
                "user_answer": body.answer.strip(),
                "is_correct": is_correct,
                "self_assessment": _rating_to_assessment(body.rating),
                "time_spent_seconds": body.time_spent_seconds,
            }).execute()

            # Update topic progress
            if topic_id:
                _update_topic_progress(client, user["id"], topic_id)

    # Calculate and award XP
    assessment = _rating_to_assessment(body.rating)
    xp_earned = calculate_problem_xp(is_correct, task_number, assessment)
    _, new_level_reached = award_xp(client, user["id"], xp_earned)

    # Record daily activity
    record_activity(
        client,
        user["id"],
        problems_solved=1,
        xp_earned=xp_earned,
    )

    # Compute retrievability for response
    retrievability = get_retrievability(updated_row, exam_date)

    return FSRSReviewResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        solution_markdown=solution_markdown,
        xp_earned=xp_earned,
        new_level_reached=new_level_reached,
        new_due=updated_row.get("due", ""),
        new_difficulty=updated_row.get("difficulty", 0),
        new_stability=updated_row.get("stability", 0),
        new_state=updated_row.get("state", ""),
        retrievability=retrievability,
    )


def _get_exam_date(client, user_id: str) -> date | None:
    """Fetch user's exam_date from the users table."""
    user_result = (
        client.table("users")
        .select("exam_date")
        .eq("id", user_id)
        .execute()
    )
    if not user_result.data:
        return None
    ed = user_result.data[0].get("exam_date")
    if ed:
        return date.fromisoformat(ed) if isinstance(ed, str) else ed
    return None


def _update_topic_progress(client, user_id: str, topic_id: str) -> None:
    """Recalculate and update strength_score for a user-topic pair."""
    attempts_result = (
        client.table("user_problem_attempts")
        .select("is_correct,problem_id")
        .eq("user_id", user_id)
        .execute()
    )
    all_attempts = attempts_result.data or []

    problems_result = (
        client.table("problems")
        .select("id")
        .eq("topic_id", topic_id)
        .execute()
    )
    topic_problem_ids = {p["id"] for p in (problems_result.data or [])}

    topic_attempts = [a for a in all_attempts if a["problem_id"] in topic_problem_ids]
    total = len(topic_attempts)
    correct = sum(1 for a in topic_attempts if a["is_correct"])
    strength = round(correct / total, 4) if total > 0 else 0.0

    now_str = datetime.now(timezone.utc).isoformat()

    existing = (
        client.table("user_topic_progress")
        .select("id")
        .eq("user_id", user_id)
        .eq("topic_id", topic_id)
        .execute()
    )

    if existing.data:
        client.table("user_topic_progress").update({
            "strength_score": strength,
            "total_attempts": total,
            "correct_attempts": correct,
            "last_practiced_at": now_str,
        }).eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("user_topic_progress").insert({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "topic_id": topic_id,
            "strength_score": strength,
            "total_attempts": total,
            "correct_attempts": correct,
            "last_practiced_at": now_str,
        }).execute()

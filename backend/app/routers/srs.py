"""SRS session endpoints: session generation with interleaving + review."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import get_current_user
from app.db.supabase_client import get_supabase_client
from app.models.srs import (
    SRSCardResponse,
    SRSReviewRequest,
    SRSReviewResponse,
    SRSSessionResponse,
)
from app.services.srs_engine import SRSCard, calculate_next_review
from app.services.streak_service import record_activity
from app.services.xp_service import award_xp, calculate_problem_xp

router = APIRouter(prefix="/api/srs", tags=["srs"])


def _interleave(cards: list[dict], max_cards: int) -> list[dict]:
    """Reorder cards so no more than 2 consecutive cards share the same topic."""
    if len(cards) <= 2:
        return cards[:max_cards]

    result: list[dict] = []
    remaining = list(cards)

    while remaining and len(result) < max_cards:
        placed = False
        for i, card in enumerate(remaining):
            # Check last 2 cards in result
            if len(result) >= 2:
                last_two_topics = [result[-1]["topic_id"], result[-2]["topic_id"]]
                if (
                    card["topic_id"] == last_two_topics[0]
                    and card["topic_id"] == last_two_topics[1]
                ):
                    continue
            result.append(remaining.pop(i))
            placed = True
            break

        if not placed:
            # All remaining are same topic — just append
            result.append(remaining.pop(0))

    return result


@router.get("/session", response_model=SRSSessionResponse)
async def get_srs_session(
    max_cards: int = Query(20, ge=1, le=50),
    user: dict = Depends(get_current_user),
) -> SRSSessionResponse:
    """Build an SRS review session from due cards.

    Cards are selected by urgency (days_since_last / interval >= 1.0),
    sorted by urgency descending, then interleaved so no more than 2
    consecutive cards share the same topic.
    """
    client = get_supabase_client()
    today = date.today()
    today_str = today.isoformat()

    # Fetch all due cards: next_review_date <= today AND status not suspended
    due_result = (
        client.table("srs_cards")
        .select("*")
        .eq("user_id", user["id"])
        .lte("next_review_date", today_str)
        .neq("status", "suspended")
        .execute()
    )
    due_cards = due_result.data or []

    # Calculate urgency for each card and sort
    for card in due_cards:
        interval = card.get("interval_days") or 1.0
        last_review = card.get("last_review_date")
        if last_review:
            if isinstance(last_review, str):
                last_dt = datetime.fromisoformat(last_review).date()
            else:
                last_dt = last_review
            days_since = (today - last_dt).days
        else:
            days_since = interval  # New card — treat as fully due
        card["_urgency"] = days_since / interval if interval > 0 else 999.0

    # Sort by urgency descending (most overdue first)
    due_cards.sort(key=lambda c: c["_urgency"], reverse=True)
    total_due = len(due_cards)

    # Interleave to avoid >2 same-topic in a row
    session_cards = _interleave(due_cards, max_cards)

    # Collect problem_ids and topic_ids for enrichment
    problem_ids = [c["problem_id"] for c in session_cards if c.get("problem_id")]
    topic_ids = list({c["topic_id"] for c in session_cards if c.get("topic_id")})

    # Fetch problems
    problems_map: dict[str, dict] = {}
    if problem_ids:
        prob_result = (
            client.table("problems")
            .select("id,problem_text,problem_images,hints,difficulty,task_number")
            .in_("id", problem_ids)
            .execute()
        )
        for p in prob_result.data or []:
            problems_map[p["id"]] = p

    # Fetch topic titles
    topics_map: dict[str, dict] = {}
    if topic_ids:
        topics_result = (
            client.table("topics")
            .select("id,title,task_number")
            .in_("id", topic_ids)
            .execute()
        )
        for t in topics_result.data or []:
            topics_map[t["id"]] = t

    # Build response
    response_cards: list[SRSCardResponse] = []
    for card in session_cards:
        problem = problems_map.get(card.get("problem_id", ""), {})
        topic = topics_map.get(card.get("topic_id", ""), {})
        response_cards.append(
            SRSCardResponse(
                card_id=card["id"],
                problem_id=card.get("problem_id", ""),
                topic_id=card.get("topic_id", ""),
                topic_title=topic.get("title"),
                task_number=topic.get("task_number", problem.get("task_number", 0)),
                card_type=card.get("card_type", "problem"),
                problem_text=problem.get("problem_text", ""),
                problem_images=problem.get("problem_images"),
                hints=problem.get("hints"),
                difficulty=problem.get("difficulty"),
                ease_factor=card.get("ease_factor", 2.5),
                interval_days=card.get("interval_days", 1.0),
                repetition_count=card.get("repetition_count", 0),
            )
        )

    return SRSSessionResponse(cards=response_cards, total_due=total_due)


@router.post("/review", response_model=SRSReviewResponse)
async def submit_review(
    body: SRSReviewRequest,
    user: dict = Depends(get_current_user),
) -> SRSReviewResponse:
    """Record an SRS review result and update the card schedule."""
    client = get_supabase_client()

    # Fetch the SRS card
    card_result = (
        client.table("srs_cards")
        .select("*")
        .eq("id", body.card_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not card_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SRS card not found",
        )

    card_row = card_result.data[0]
    problem_id = card_row.get("problem_id")
    topic_id = card_row.get("topic_id", "")

    # Fetch problem for answer checking
    is_correct = False
    correct_answer: str | None = None
    solution_markdown: str | None = None
    task_number = 0

    if problem_id:
        prob_result = (
            client.table("problems")
            .select("correct_answer,solution_markdown,task_number")
            .eq("id", problem_id)
            .execute()
        )
        if prob_result.data:
            correct_answer = (prob_result.data[0].get("correct_answer") or "").strip()
            solution_markdown = prob_result.data[0].get("solution_markdown")
            task_number = prob_result.data[0].get("task_number", 0)

            # Check answer if provided
            user_answer = body.answer.strip()
            if user_answer and correct_answer:
                is_correct = user_answer.lower() == correct_answer.lower()

    # Fetch user's exam_date for countdown factor
    user_result = (
        client.table("users")
        .select("exam_date")
        .eq("id", user["id"])
        .execute()
    )
    exam_date: date | None = None
    if user_result.data:
        ed = user_result.data[0].get("exam_date")
        if ed:
            exam_date = date.fromisoformat(ed) if isinstance(ed, str) else ed

    # Calculate next review using SRS engine
    srs_card = SRSCard(
        ease_factor=card_row.get("ease_factor", 2.5),
        interval_days=card_row.get("interval_days", 1.0),
        repetition_count=card_row.get("repetition_count", 0),
    )

    review_result = calculate_next_review(
        card=srs_card,
        self_assessment=body.self_assessment.value,
        exam_date=exam_date,
    )

    # Update the SRS card
    today_str = date.today().isoformat()
    new_status = "review"
    if body.self_assessment.value == "again":
        new_status = "learning"

    client.table("srs_cards").update({
        "ease_factor": review_result.new_ease_factor,
        "interval_days": review_result.new_interval,
        "repetition_count": srs_card.repetition_count + 1,
        "next_review_date": review_result.next_review_date.isoformat(),
        "last_review_date": today_str,
        "status": new_status,
    }).eq("id", body.card_id).execute()

    # Record attempt if problem-based card
    if problem_id:
        client.table("user_problem_attempts").insert({
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "problem_id": problem_id,
            "user_answer": body.answer.strip(),
            "is_correct": is_correct,
            "self_assessment": body.self_assessment.value,
            "time_spent_seconds": body.time_spent_seconds,
        }).execute()

    # Calculate and award XP
    xp_earned = calculate_problem_xp(
        is_correct, task_number, body.self_assessment.value,
    )
    _, new_level_reached = award_xp(client, user["id"], xp_earned)

    # Update user_topic_progress strength_score
    if topic_id:
        _update_topic_progress(client, user["id"], topic_id)

    # Record daily activity and update streak
    record_activity(
        client,
        user["id"],
        problems_solved=1,
        xp_earned=xp_earned,
    )

    return SRSReviewResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        solution_markdown=solution_markdown,
        xp_earned=xp_earned,
        new_level_reached=new_level_reached,
        next_review_date=review_result.next_review_date.isoformat(),
        new_interval=review_result.new_interval,
        new_ease_factor=review_result.new_ease_factor,
    )


def _update_topic_progress(client, user_id: str, topic_id: str) -> None:
    """Recalculate and update strength_score for a user-topic pair."""
    # Get all attempts for this topic's problems
    attempts_result = (
        client.table("user_problem_attempts")
        .select("is_correct,problem_id")
        .eq("user_id", user_id)
        .execute()
    )
    all_attempts = attempts_result.data or []

    # Get problem IDs for this topic
    problems_result = (
        client.table("problems")
        .select("id")
        .eq("topic_id", topic_id)
        .execute()
    )
    topic_problem_ids = {p["id"] for p in (problems_result.data or [])}

    # Filter attempts for this topic
    topic_attempts = [a for a in all_attempts if a["problem_id"] in topic_problem_ids]
    total = len(topic_attempts)
    correct = sum(1 for a in topic_attempts if a["is_correct"])
    strength = round(correct / total, 4) if total > 0 else 0.0

    now_str = datetime.now(timezone.utc).isoformat()

    # Upsert user_topic_progress
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


def _ensure_srs_card(
    client, user_id: str, problem_id: str, topic_id: str,
) -> str:
    """Create an SRS card for a problem if one doesn't exist. Returns card ID."""
    existing = (
        client.table("srs_cards")
        .select("id")
        .eq("user_id", user_id)
        .eq("problem_id", problem_id)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    card_id = str(uuid.uuid4())
    today_str = date.today().isoformat()
    client.table("srs_cards").insert({
        "id": card_id,
        "user_id": user_id,
        "problem_id": problem_id,
        "topic_id": topic_id,
        "card_type": "problem",
        "ease_factor": 2.5,
        "interval_days": 1.0,
        "repetition_count": 0,
        "next_review_date": today_str,
        "last_review_date": None,
        "status": "new",
    }).execute()
    return card_id

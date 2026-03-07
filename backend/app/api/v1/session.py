"""Session API: generate daily review session and record review answers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from supabase import Client

from app.api.deps import CurrentUser
from app.core.session.generator import SessionGenerator
from app.db.supabase import get_supabase_client
from app.services.review_service import process_review

router = APIRouter()


class ReviewRequest(BaseModel):
    card_id: str = Field(..., description="UUID of the card being reviewed")
    session_id: str = Field(..., description="UUID of the active study session")
    rating: int = Field(..., ge=1, le=4, description="1=Again, 2=Hard, 3=Good, 4=Easy")
    hints_used: int = Field(default=0, ge=0, description="Number of hints revealed")
    response_time_ms: int | None = Field(
        default=None, ge=0, description="Response time in milliseconds"
    )


@router.post("/session/generate")
def generate_session(
    current_user: CurrentUser,
    topic_id: str | None = Query(default=None, description="Restrict to a single topic"),
    sb: Client = Depends(get_supabase_client),
) -> dict[str, Any]:
    """Generate a daily review session for the authenticated user.

    Returns a session_id and an ordered list of cards (due + new),
    interleaved so no topic appears more than twice in a row.
    """
    user_id: str = current_user["user_id"]

    # Fetch user settings; fall back to 30-minute goal if row not yet created
    user_resp = (
        sb.table("users")
        .select("daily_goal_minutes")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    daily_goal: int = (user_resp.data or {}).get("daily_goal_minutes") or 30

    # Generate card list
    generator = SessionGenerator(sb)
    cards = generator.generate(
        user_id=user_id,
        daily_goal_minutes=daily_goal,
        topic_id=topic_id,
    )

    # Create a study_session record to track this session
    session_id = str(uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    sb.table("study_sessions").insert(
        {
            "id": session_id,
            "user_id": user_id,
            "session_type": "daily",
            "started_at": now_iso,
            "cards_reviewed": 0,
            "cards_correct": 0,
            "cards_incorrect": 0,
        }
    ).execute()

    return {
        "session_id": session_id,
        "cards": cards,
        "total_cards": len(cards),
        "daily_goal_minutes": daily_goal,
    }


@router.post("/session/review")
def review_card(
    body: ReviewRequest,
    current_user: CurrentUser,
    sb: Client = Depends(get_supabase_client),
) -> dict[str, Any]:
    """Record a user's answer rating for a card and update FSRS scheduling.

    Accepts card_id, session_id, rating (1–4), hints_used, response_time_ms.
    Updates user_card_progress, inserts a review_logs record, and increments
    study_sessions counters.

    Returns updated scheduling info: next_due, stability, difficulty, etc.
    """
    user_id: str = current_user["user_id"]

    try:
        result = process_review(
            sb=sb,
            user_id=user_id,
            card_id=body.card_id,
            session_id=body.session_id,
            rating=body.rating,
            hints_used=body.hints_used,
            response_time_ms=body.response_time_ms,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return result

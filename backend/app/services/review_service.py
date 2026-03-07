"""Review service: process a card rating, update FSRS state and logs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from supabase import Client

from app.core.fsrs.engine import FSRSEngine

_engine = FSRSEngine()


def process_review(
    sb: Client,
    user_id: str,
    card_id: str,
    session_id: str,
    rating: int,
    hints_used: int = 0,
    response_time_ms: int | None = None,
) -> dict[str, Any]:
    """Process a card review answer for a user.

    Steps:
    1. Fetch existing user_card_progress (may not exist for a new card).
    2. Run FSRS engine to compute next scheduling parameters.
    3. Upsert user_card_progress with new FSRS fields.
    4. Insert an immutable review_logs record.
    5. Increment study_sessions counters (cards_reviewed, correct/incorrect).

    Args:
        sb: Supabase service-role client.
        user_id: Authenticated user UUID.
        card_id: Card being reviewed.
        session_id: Current study session UUID.
        rating: User rating 1–4 (1=Again, 2=Hard, 3=Good, 4=Easy).
        hints_used: Number of hints revealed during this review.
        response_time_ms: Time taken to respond in milliseconds (optional).

    Returns:
        Dict with: next_due, stability, difficulty, fsrs_state, review_count.
    """
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # 1. Fetch existing progress (None means card is new for this user)
    # ------------------------------------------------------------------
    prog_resp = (
        sb.table("user_card_progress")
        .select(
            "id, fsrs_state, stability, difficulty, due_date, "
            "last_reviewed_at, interval_days, reps, lapses"
        )
        .eq("user_id", user_id)
        .eq("card_id", card_id)
        .maybe_single()
        .execute()
    )
    existing: dict[str, Any] = prog_resp.data or {}

    # Build card_progress dict in the shape FSRSEngine expects
    card_progress: dict[str, Any] = {
        "stability": existing.get("stability"),
        "difficulty": existing.get("difficulty"),
        "fsrs_state": existing.get("fsrs_state") or "new",
        "due_date": existing.get("due_date"),
        "last_review": existing.get("last_reviewed_at"),
        "review_count": existing.get("reps") or 0,
    }

    # ------------------------------------------------------------------
    # 2. Run FSRS scheduling
    # ------------------------------------------------------------------
    scheduled = _engine.schedule(card_progress, rating)

    # ------------------------------------------------------------------
    # 3. Upsert user_card_progress
    # ------------------------------------------------------------------
    lapses_before: int = existing.get("lapses") or 0
    new_lapses = lapses_before + (1 if rating == 1 else 0)

    due_date_iso = _to_iso(scheduled["due_date"])
    last_reviewed_iso = _to_iso(scheduled["last_review"])

    ucp_payload: dict[str, Any] = {
        "user_id": user_id,
        "card_id": card_id,
        "fsrs_state": scheduled["fsrs_state"],
        "stability": scheduled["stability"],
        "difficulty": scheduled["difficulty"],
        "due_date": due_date_iso,
        "last_reviewed_at": last_reviewed_iso,
        "interval_days": scheduled["scheduled_days"],
        "reps": scheduled["review_count"],
        "lapses": new_lapses,
    }

    if existing.get("id"):
        # UPDATE existing row
        sb.table("user_card_progress").update(ucp_payload).eq(
            "id", existing["id"]
        ).execute()
    else:
        # INSERT new row
        sb.table("user_card_progress").insert(ucp_payload).execute()

    # ------------------------------------------------------------------
    # 4. Insert review_logs (immutable)
    # ------------------------------------------------------------------
    interval_before = existing.get("interval_days")
    log_payload: dict[str, Any] = {
        "id": str(uuid4()),
        "user_id": user_id,
        "card_id": card_id,
        "session_id": session_id,
        "rating": rating,
        "fsrs_state_before": card_progress["fsrs_state"],
        "fsrs_state_after": scheduled["fsrs_state"],
        "stability_before": existing.get("stability"),
        "stability_after": scheduled["stability"],
        "interval_before": float(interval_before) if interval_before is not None else None,
        "interval_after": scheduled["scheduled_days"],
        "due_date_after": due_date_iso,
        "hints_used": hints_used,
        "response_time_ms": response_time_ms,
        "reviewed_at": _to_iso(now),
    }
    sb.table("review_logs").insert(log_payload).execute()

    # ------------------------------------------------------------------
    # 5. Update study_sessions counters
    # ------------------------------------------------------------------
    is_correct = rating >= 3
    _increment_session_counters(sb, session_id, is_correct)

    # ------------------------------------------------------------------
    # 6. FIRe: propagate credit upstream (rating >= 3) or penalty downstream (rating == 1)
    # ------------------------------------------------------------------
    if is_correct:
        _fire_propagate_credit(sb, user_id, card_id)
    elif rating == 1:
        _fire_propagate_penalty(sb, user_id, card_id)

    return {
        "next_due": due_date_iso,
        "stability": scheduled["stability"],
        "difficulty": scheduled["difficulty"],
        "fsrs_state": scheduled["fsrs_state"],
        "review_count": scheduled["review_count"],
        "interval_days": scheduled["scheduled_days"],
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _fire_propagate_credit(sb: Client, user_id: str, card_id: str) -> None:
    """Look up the card's topic and propagate FIRe credit upstream."""
    from app.core.fire.graph import KnowledgeGraph
    from app.core.fire.propagator import propagate_credit

    card_resp = (
        sb.table("cards").select("topic_id").eq("id", card_id).maybe_single().execute()
    )
    if not card_resp.data:
        return
    topic_id: str | None = card_resp.data.get("topic_id")
    if not topic_id:
        return

    graph = KnowledgeGraph.from_supabase(sb)
    propagate_credit(sb, user_id, topic_id, credit=1.0, graph=graph)


def _fire_propagate_penalty(sb: Client, user_id: str, card_id: str) -> None:
    """Look up the card's topic and propagate FIRe penalty downstream."""
    from app.core.fire.graph import KnowledgeGraph
    from app.core.fire.propagator import propagate_penalty_up

    card_resp = (
        sb.table("cards").select("topic_id").eq("id", card_id).maybe_single().execute()
    )
    if not card_resp.data:
        return
    topic_id: str | None = card_resp.data.get("topic_id")
    if not topic_id:
        return

    graph = KnowledgeGraph.from_supabase(sb)
    propagate_penalty_up(sb, user_id, topic_id, penalty=1.0, graph=graph)


def _to_iso(value: datetime | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _increment_session_counters(sb: Client, session_id: str, is_correct: bool) -> None:
    """Atomically increment session review counters via a single update."""
    resp = (
        sb.table("study_sessions")
        .select("cards_reviewed, cards_correct, cards_incorrect")
        .eq("id", session_id)
        .maybe_single()
        .execute()
    )
    row = resp.data or {}
    reviewed = (row.get("cards_reviewed") or 0) + 1
    correct = (row.get("cards_correct") or 0) + (1 if is_correct else 0)
    incorrect = (row.get("cards_incorrect") or 0) + (0 if is_correct else 1)

    sb.table("study_sessions").update(
        {
            "cards_reviewed": reviewed,
            "cards_correct": correct,
            "cards_incorrect": incorrect,
        }
    ).eq("id", session_id).execute()

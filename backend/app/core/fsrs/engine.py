"""FSRS-5 engine wrapping py-fsrs for Repeatify card scheduling."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fsrs import FSRS, Card, Rating, State

# Map our DB rating integers to py-fsrs Rating enum
_RATING_MAP: dict[int, Rating] = {
    1: Rating.Again,
    2: Rating.Hard,
    3: Rating.Good,
    4: Rating.Easy,
}

# Map py-fsrs State enum to our DB fsrs_state strings
_STATE_MAP: dict[State, str] = {
    State.New: "new",
    State.Learning: "learning",
    State.Review: "review",
    State.Relearning: "relearning",
}

# Map our DB fsrs_state strings to py-fsrs State enum
_STATE_REVERSE_MAP: dict[str, State] = {v: k for k, v in _STATE_MAP.items()}


class FSRSEngine:
    """Wrapper around py-fsrs providing schedule() for a single card review."""

    def __init__(self) -> None:
        self._fsrs = FSRS()

    def schedule(self, card_progress: dict[str, Any], rating: int) -> dict[str, Any]:
        """Calculate next review parameters after a user rates a card.

        Args:
            card_progress: Row from user_card_progress with FSRS fields.
                Required keys: stability, difficulty, fsrs_state, due_date,
                last_review, review_count.  All may be None for a new card.
            rating: User rating 1–4 (1=Again, 2=Hard, 3=Good, 4=Easy).

        Returns:
            Dict with updated FSRS fields ready to write back to the DB:
            stability, difficulty, fsrs_state, due_date, last_review,
            review_count, scheduled_days, elapsed_days.
        """
        if rating not in _RATING_MAP:
            raise ValueError(f"Invalid rating {rating!r}. Must be 1–4.")

        fsrs_rating = _RATING_MAP[rating]
        card = self._build_card(card_progress)
        now = datetime.now(timezone.utc)

        scheduling_cards = self._fsrs.repeat(card, now)
        updated: Card = scheduling_cards[fsrs_rating].card

        return {
            "stability": round(updated.stability, 6),
            "difficulty": round(updated.difficulty, 6),
            "fsrs_state": _STATE_MAP[updated.state],
            "due_date": updated.due,
            "last_review": now,
            "review_count": (card_progress.get("review_count") or 0) + 1,
            "scheduled_days": updated.scheduled_days,
            "elapsed_days": updated.elapsed_days,
        }

    def preview_ratings(self, card_progress: dict[str, Any]) -> dict[int, dict[str, Any]]:
        """Return scheduled results for all 4 ratings without persisting.

        Useful for optimistic UI preview of next due dates.
        """
        card = self._build_card(card_progress)
        now = datetime.now(timezone.utc)
        scheduling_cards = self._fsrs.repeat(card, now)

        result: dict[int, dict[str, Any]] = {}
        for rating_int, fsrs_rating in _RATING_MAP.items():
            updated: Card = scheduling_cards[fsrs_rating].card
            result[rating_int] = {
                "stability": round(updated.stability, 6),
                "difficulty": round(updated.difficulty, 6),
                "fsrs_state": _STATE_MAP[updated.state],
                "due_date": updated.due,
                "scheduled_days": updated.scheduled_days,
            }
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_card(card_progress: dict[str, Any]) -> Card:
        """Reconstruct a py-fsrs Card from DB fields."""
        card = Card()

        state_str = card_progress.get("fsrs_state") or "new"
        card.state = _STATE_REVERSE_MAP.get(state_str, State.New)

        stability = card_progress.get("stability")
        if stability is not None:
            card.stability = float(stability)

        difficulty = card_progress.get("difficulty")
        if difficulty is not None:
            card.difficulty = float(difficulty)

        due = card_progress.get("due_date")
        if due is not None:
            if isinstance(due, str):
                due = datetime.fromisoformat(due)
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            card.due = due

        last_review = card_progress.get("last_review")
        if last_review is not None:
            if isinstance(last_review, str):
                last_review = datetime.fromisoformat(last_review)
            if last_review.tzinfo is None:
                last_review = last_review.replace(tzinfo=timezone.utc)
            card.last_review = last_review

        return card

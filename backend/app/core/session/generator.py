"""Session generator: selects due + new cards, applies limits and interleaving."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from supabase import Client

from app.core.session.interleaver import interleave

# Approximate seconds per card type (used to estimate session card count)
_SECONDS_PER_CARD: dict[str, float] = {
    "basic_qa": 30,
    "step_by_step": 90,
}
_DEFAULT_SECONDS_PER_CARD = 45

_MAX_CARDS_PER_SESSION = 50
_MIN_CARDS_PER_SESSION = 5


class SessionGenerator:
    """Generates a daily review session card list for a given user."""

    def __init__(self, supabase: Client) -> None:
        self._sb = supabase

    def generate(
        self,
        user_id: str,
        daily_goal_minutes: int = 30,
        topic_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return an ordered list of card dicts ready for the session.

        Args:
            user_id: Authenticated user's UUID.
            daily_goal_minutes: User's daily goal in minutes.
            topic_id: If set, restrict session to this topic only.

        Returns:
            List of card dicts with embedded progress fields, interleaved by topic.
        """
        target = self._target_count(daily_goal_minutes)

        due_cards = self._fetch_due_cards(user_id, topic_id)
        new_cards: list[dict[str, Any]] = []
        if len(due_cards) < target:
            new_cards = self._fetch_new_cards(
                user_id, limit=target - len(due_cards), topic_id=topic_id
            )

        # Sort due cards by urgency (most overdue first), then append new cards
        sorted_due = _sort_by_urgency(due_cards)
        combined = (sorted_due + new_cards)[:target]

        return interleave(combined, max_consecutive=2)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _target_count(daily_goal_minutes: int) -> int:
        seconds = daily_goal_minutes * 60
        count = math.floor(seconds / _DEFAULT_SECONDS_PER_CARD)
        return max(_MIN_CARDS_PER_SESSION, min(_MAX_CARDS_PER_SESSION, count))

    def _fetch_due_cards(
        self, user_id: str, topic_id: str | None
    ) -> list[dict[str, Any]]:
        """Fetch cards with due_date <= now from user_card_progress."""
        now = datetime.now(timezone.utc).isoformat()
        query = (
            self._sb.table("user_card_progress")
            .select(
                "card_id, stability, difficulty, fsrs_state, due_date, last_review, "
                "review_count, scheduled_days, elapsed_days, "
                "cards("
                "  id, topic_id, card_type, question_text, answer_text,"
                "  question_image_url, answer_image_url, solution_steps, hints,"
                "  difficulty, ege_task_number,"
                "  topics(code, title)"
                ")"
            )
            .eq("user_id", user_id)
            .lte("due_date", now)
            .neq("fsrs_state", "new")
        )
        if topic_id:
            query = query.eq("cards.topic_id", topic_id)

        resp = query.execute()
        return _flatten_progress_rows(resp.data or [])

    def _fetch_new_cards(
        self, user_id: str, limit: int, topic_id: str | None
    ) -> list[dict[str, Any]]:
        """Fetch cards the user has not yet reviewed."""
        # Get IDs of cards already seen by this user
        seen_resp = (
            self._sb.table("user_card_progress")
            .select("card_id")
            .eq("user_id", user_id)
            .execute()
        )
        seen_ids: list[str] = [r["card_id"] for r in (seen_resp.data or [])]

        query = (
            self._sb.table("cards")
            .select(
                "id, topic_id, card_type, question_text, answer_text,"
                "question_image_url, answer_image_url, solution_steps, hints,"
                "difficulty, ege_task_number,"
                "topics(code, title)"
            )
            .order("difficulty", desc=False)
            .limit(limit)
        )
        if topic_id:
            query = query.eq("topic_id", topic_id)
        if seen_ids:
            query = query.not_.in_("id", seen_ids)

        resp = query.execute()
        return _flatten_card_rows(resp.data or [])


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _sort_by_urgency(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort due cards most-overdue first (largest positive elapsed days since due)."""
    now = datetime.now(timezone.utc)

    def _overdue_seconds(card: dict[str, Any]) -> float:
        progress = card.get("progress") or {}
        due = progress.get("due_date")
        if due is None:
            return 0.0
        if isinstance(due, str):
            due = datetime.fromisoformat(due)
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        return (now - due).total_seconds()

    return sorted(cards, key=_overdue_seconds, reverse=True)


def _flatten_progress_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge user_card_progress rows with their nested card + topic data."""
    result: list[dict[str, Any]] = []
    for row in rows:
        card_data: dict[str, Any] = row.get("cards") or {}
        topic_data: dict[str, Any] = card_data.pop("topics", {}) or {}
        flat: dict[str, Any] = {
            "card_id": row.get("card_id"),
            "topic_id": card_data.get("topic_id"),
            "topic_code": topic_data.get("code"),
            "topic_title": topic_data.get("title"),
            "card_type": card_data.get("card_type"),
            "question_text": card_data.get("question_text"),
            "answer_text": card_data.get("answer_text"),
            "question_image_url": card_data.get("question_image_url"),
            "answer_image_url": card_data.get("answer_image_url"),
            "solution_steps": card_data.get("solution_steps"),
            "hints": card_data.get("hints") or [],
            "difficulty": card_data.get("difficulty"),
            "ege_task_number": card_data.get("ege_task_number"),
            "progress": {
                "stability": row.get("stability"),
                "difficulty": row.get("difficulty"),
                "fsrs_state": row.get("fsrs_state"),
                "due_date": row.get("due_date"),
                "last_review": row.get("last_review"),
                "review_count": row.get("review_count") or 0,
                "scheduled_days": row.get("scheduled_days"),
                "elapsed_days": row.get("elapsed_days"),
            },
        }
        result.append(flat)
    return result


def _flatten_card_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flatten raw card rows (no user_card_progress yet, state='new')."""
    result: list[dict[str, Any]] = []
    for row in rows:
        topic_data: dict[str, Any] = (row.pop("topics", None) or {})
        flat: dict[str, Any] = {
            "card_id": row.get("id"),
            "topic_id": row.get("topic_id"),
            "topic_code": topic_data.get("code"),
            "topic_title": topic_data.get("title"),
            "card_type": row.get("card_type"),
            "question_text": row.get("question_text"),
            "answer_text": row.get("answer_text"),
            "question_image_url": row.get("question_image_url"),
            "answer_image_url": row.get("answer_image_url"),
            "solution_steps": row.get("solution_steps"),
            "hints": row.get("hints") or [],
            "difficulty": row.get("difficulty"),
            "ege_task_number": row.get("ege_task_number"),
            "progress": {
                "stability": None,
                "difficulty": None,
                "fsrs_state": "new",
                "due_date": None,
                "last_review": None,
                "review_count": 0,
                "scheduled_days": None,
                "elapsed_days": None,
            },
        }
        result.append(flat)
    return result

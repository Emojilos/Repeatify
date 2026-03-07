"""Unit tests for review_service (TASK-015)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.services.review_service import _increment_session_counters, _to_iso, process_review


# ---------------------------------------------------------------------------
# Helper: build a mock Supabase client
# ---------------------------------------------------------------------------


def _mock_sb(existing_progress: dict | None = None, session_row: dict | None = None):
    """Return a MagicMock Supabase client with configurable query results."""
    sb = MagicMock()

    # user_card_progress lookup
    prog_chain = sb.table("user_card_progress").select.return_value
    prog_chain.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
        existing_progress
    )

    # study_sessions counters lookup
    sess_chain = sb.table("study_sessions").select.return_value
    sess_chain.eq.return_value.maybe_single.return_value.execute.return_value.data = (
        session_row or {"cards_reviewed": 0, "cards_correct": 0, "cards_incorrect": 0}
    )

    return sb


# ---------------------------------------------------------------------------
# _to_iso helper
# ---------------------------------------------------------------------------


def test_to_iso_none():
    assert _to_iso(None) is None


def test_to_iso_string_passthrough():
    s = "2026-01-01T00:00:00+00:00"
    assert _to_iso(s) == s


def test_to_iso_datetime():
    dt = datetime(2026, 3, 7, 12, 0, 0, tzinfo=timezone.utc)
    result = _to_iso(dt)
    assert "2026-03-07" in result
    assert "12:00:00" in result


# ---------------------------------------------------------------------------
# _increment_session_counters helper
# ---------------------------------------------------------------------------


def test_increment_session_counters_correct():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 5,
        "cards_correct": 3,
        "cards_incorrect": 2,
    }

    _increment_session_counters(sb, "session-123", is_correct=True)

    sb.table.return_value.update.assert_called_once_with(
        {"cards_reviewed": 6, "cards_correct": 4, "cards_incorrect": 2}
    )


def test_increment_session_counters_incorrect():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 2,
        "cards_correct": 1,
        "cards_incorrect": 1,
    }

    _increment_session_counters(sb, "session-456", is_correct=False)

    sb.table.return_value.update.assert_called_once_with(
        {"cards_reviewed": 3, "cards_correct": 1, "cards_incorrect": 2}
    )


def test_increment_session_counters_handles_none_data():
    """Session row not found yet → treat all counters as 0."""
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None

    _increment_session_counters(sb, "session-789", is_correct=True)

    sb.table.return_value.update.assert_called_once_with(
        {"cards_reviewed": 1, "cards_correct": 1, "cards_incorrect": 0}
    )


# ---------------------------------------------------------------------------
# process_review — new card (no existing progress)
# ---------------------------------------------------------------------------


def test_process_review_new_card_good_rating():
    """Rating=3 on a new card should return a future due_date."""
    sb = MagicMock()

    # No existing progress
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    # Session counters
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 0,
        "cards_correct": 0,
        "cards_incorrect": 0,
    }

    result = process_review(
        sb=sb,
        user_id="user-1",
        card_id="card-1",
        session_id="session-1",
        rating=3,
        hints_used=0,
        response_time_ms=5000,
    )

    assert result["fsrs_state"] in ("learning", "review", "new")
    assert result["review_count"] == 1
    assert result["next_due"] is not None
    assert result["stability"] > 0
    assert result["difficulty"] > 0


def test_process_review_new_card_again_rating():
    """Rating=1 (Again) on new card → fsrs_state learning, lapses incremented."""
    sb = MagicMock()

    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 0,
        "cards_correct": 0,
        "cards_incorrect": 0,
    }

    result = process_review(
        sb=sb,
        user_id="user-1",
        card_id="card-2",
        session_id="session-1",
        rating=1,
        hints_used=2,
    )

    assert result["review_count"] == 1
    # lapses=1 should be written — verify insert was called with lapses=1
    insert_call_args = sb.table.return_value.insert.call_args
    assert insert_call_args is not None
    payload = insert_call_args[0][0]
    assert payload["lapses"] == 1


def test_process_review_existing_card_updates_row():
    """When progress row exists, UPDATE should be called (not INSERT)."""
    sb = MagicMock()

    existing = {
        "id": "prog-uuid-1",
        "fsrs_state": "review",
        "stability": 5.0,
        "difficulty": 0.3,
        "due_date": "2026-03-06T00:00:00+00:00",
        "last_reviewed_at": "2026-02-24T00:00:00+00:00",
        "interval_days": 10,
        "reps": 5,
        "lapses": 0,
    }
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = existing
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 3,
        "cards_correct": 3,
        "cards_incorrect": 0,
    }

    result = process_review(
        sb=sb,
        user_id="user-2",
        card_id="card-3",
        session_id="session-2",
        rating=4,
        hints_used=0,
    )

    # With Good/Easy rating the interval should grow
    assert result["interval_days"] > 10
    assert result["review_count"] == 6  # reps was 5


def test_process_review_rating_1_existing_card_increments_lapses():
    """Rating=1 on existing card should add 1 lapse."""
    sb = MagicMock()

    existing = {
        "id": "prog-uuid-2",
        "fsrs_state": "review",
        "stability": 8.0,
        "difficulty": 0.4,
        "due_date": "2026-03-01T00:00:00+00:00",
        "last_reviewed_at": "2026-02-20T00:00:00+00:00",
        "interval_days": 9,
        "reps": 4,
        "lapses": 1,
    }
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = existing
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 2,
        "cards_correct": 2,
        "cards_incorrect": 0,
    }

    process_review(
        sb=sb,
        user_id="user-3",
        card_id="card-4",
        session_id="session-3",
        rating=1,
    )

    # UPDATE call should include lapses=2
    update_call = sb.table.return_value.update.call_args
    assert update_call is not None
    payload = update_call[0][0]
    assert payload["lapses"] == 2


def test_process_review_invalid_rating_raises():
    """Rating outside 1–4 should raise ValueError from FSRSEngine."""
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None

    with pytest.raises(ValueError, match="Invalid rating"):
        process_review(
            sb=sb,
            user_id="user-x",
            card_id="card-x",
            session_id="session-x",
            rating=5,
        )


def test_process_review_inserts_review_log():
    """A review_logs insert must happen for every process_review call."""
    sb = MagicMock()

    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    sb.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
        "cards_reviewed": 0,
        "cards_correct": 0,
        "cards_incorrect": 0,
    }

    process_review(
        sb=sb,
        user_id="user-4",
        card_id="card-5",
        session_id="session-4",
        rating=2,
        hints_used=1,
        response_time_ms=12000,
    )

    # review_logs insert must have been called
    insert_calls = [
        c for c in sb.table.return_value.insert.call_args_list
    ]
    # At least one insert call should have a payload with "reviewed_at"
    log_inserts = [
        c for c in insert_calls
        if "reviewed_at" in (c[0][0] if c[0] else {})
    ]
    assert len(log_inserts) >= 1
    log_payload = log_inserts[0][0][0]
    assert log_payload["hints_used"] == 1
    assert log_payload["response_time_ms"] == 12000
    assert log_payload["rating"] == 2

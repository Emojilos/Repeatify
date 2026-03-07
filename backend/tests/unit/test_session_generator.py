"""Unit tests for session generator and interleaver (TASK-014)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.session.generator import (
    SessionGenerator,
    _flatten_card_rows,
    _flatten_progress_rows,
    _sort_by_urgency,
)
from app.core.session.interleaver import interleave


# ---------------------------------------------------------------------------
# Interleaver tests (pure Python, no mocks needed)
# ---------------------------------------------------------------------------


def _make_card(card_id: str, topic_id: str) -> dict:
    return {"card_id": card_id, "topic_id": topic_id}


def test_interleave_empty():
    assert interleave([]) == []


def test_interleave_single_topic_respects_max_consecutive():
    cards = [_make_card(f"c{i}", "topic-A") for i in range(6)]
    result = interleave(cards, max_consecutive=2)
    # All cards from same topic — constraint can't fully be satisfied,
    # but output should contain all cards
    assert len(result) == 6


def test_interleave_two_topics_no_more_than_two_consecutive():
    cards = (
        [_make_card(f"a{i}", "topic-A") for i in range(4)]
        + [_make_card(f"b{i}", "topic-B") for i in range(4)]
    )
    result = interleave(cards, max_consecutive=2)
    assert len(result) == 8

    consecutive = 1
    for i in range(1, len(result)):
        if result[i]["topic_id"] == result[i - 1]["topic_id"]:
            consecutive += 1
            assert consecutive <= 2, (
                f"Topic {result[i]['topic_id']} appeared {consecutive} times consecutively"
            )
        else:
            consecutive = 1


def test_interleave_three_topics_constraint():
    cards = (
        [_make_card(f"a{i}", "A") for i in range(3)]
        + [_make_card(f"b{i}", "B") for i in range(3)]
        + [_make_card(f"c{i}", "C") for i in range(3)]
    )
    result = interleave(cards, max_consecutive=2)
    assert len(result) == 9

    consecutive = 1
    for i in range(1, len(result)):
        if result[i]["topic_id"] == result[i - 1]["topic_id"]:
            consecutive += 1
            assert consecutive <= 2
        else:
            consecutive = 1


def test_interleave_preserves_all_cards():
    cards = (
        [_make_card(f"a{i}", "A") for i in range(5)]
        + [_make_card(f"b{i}", "B") for i in range(5)]
    )
    result = interleave(cards, max_consecutive=2)
    assert len(result) == 10
    result_ids = {c["card_id"] for c in result}
    original_ids = {c["card_id"] for c in cards}
    assert result_ids == original_ids


# ---------------------------------------------------------------------------
# _sort_by_urgency tests
# ---------------------------------------------------------------------------


def _progress_card(card_id: str, due_days_ago: float) -> dict:
    now = datetime.now(timezone.utc)
    due = now - timedelta(days=due_days_ago)
    return {
        "card_id": card_id,
        "topic_id": "topic-X",
        "progress": {"due_date": due.isoformat()},
    }


def test_sort_by_urgency_most_overdue_first():
    cards = [
        _progress_card("c1", due_days_ago=1),
        _progress_card("c2", due_days_ago=5),
        _progress_card("c3", due_days_ago=0.1),
    ]
    result = _sort_by_urgency(cards)
    assert result[0]["card_id"] == "c2"  # 5 days overdue
    assert result[1]["card_id"] == "c1"  # 1 day overdue
    assert result[2]["card_id"] == "c3"  # 0.1 days overdue


# ---------------------------------------------------------------------------
# _target_count tests
# ---------------------------------------------------------------------------


def test_target_count_15_minutes():
    count = SessionGenerator._target_count(15)
    # 15*60/45 = 20 cards
    assert count == 20


def test_target_count_30_minutes():
    count = SessionGenerator._target_count(30)
    # 30*60/45 = 40 cards
    assert count == 40


def test_target_count_minimum_enforced():
    # 0 minutes → minimum kicks in
    count = SessionGenerator._target_count(0)
    assert count == 5


def test_target_count_maximum_enforced():
    # 120 minutes would be 160 cards → capped at 50
    count = SessionGenerator._target_count(120)
    assert count == 50


# ---------------------------------------------------------------------------
# _flatten helpers
# ---------------------------------------------------------------------------


def test_flatten_card_rows_sets_new_state():
    raw = [
        {
            "id": "card-1",
            "topic_id": "topic-1",
            "card_type": "basic_qa",
            "question_text": "Q",
            "answer_text": "A",
            "question_image_url": None,
            "answer_image_url": None,
            "solution_steps": None,
            "hints": [],
            "difficulty": 0.3,
            "ege_task_number": 5,
            "topics": {"code": "ALG.LIN", "title": "Линейные уравнения"},
        }
    ]
    result = _flatten_card_rows(raw)
    assert len(result) == 1
    assert result[0]["card_id"] == "card-1"
    assert result[0]["progress"]["fsrs_state"] == "new"
    assert result[0]["topic_code"] == "ALG.LIN"
    assert result[0]["progress"]["review_count"] == 0


def test_flatten_progress_rows_merges_fields():
    raw = [
        {
            "card_id": "card-2",
            "stability": 5.0,
            "difficulty": 4.0,
            "fsrs_state": "review",
            "due_date": "2026-01-01T00:00:00+00:00",
            "last_review": "2025-12-22T00:00:00+00:00",
            "review_count": 3,
            "scheduled_days": 10,
            "elapsed_days": 10,
            "cards": {
                "id": "card-2",
                "topic_id": "topic-2",
                "card_type": "basic_qa",
                "question_text": "Question",
                "answer_text": "Answer",
                "question_image_url": None,
                "answer_image_url": None,
                "solution_steps": None,
                "hints": [],
                "difficulty": 0.5,
                "ege_task_number": 3,
                "topics": {"code": "GEO.PLAN", "title": "Планиметрия"},
            },
        }
    ]
    result = _flatten_progress_rows(raw)
    assert len(result) == 1
    r = result[0]
    assert r["card_id"] == "card-2"
    assert r["topic_code"] == "GEO.PLAN"
    assert r["progress"]["fsrs_state"] == "review"
    assert r["progress"]["review_count"] == 3


# ---------------------------------------------------------------------------
# SessionGenerator integration test (mocked Supabase)
# ---------------------------------------------------------------------------


def _mock_execute(data: list) -> MagicMock:
    resp = MagicMock()
    resp.data = data
    return resp


def test_generator_returns_due_and_new_cards():
    now = datetime.now(timezone.utc)

    # Build mock Supabase client
    sb = MagicMock()

    # user_card_progress query (due cards)
    due_rows = [
        {
            "card_id": "due-card-1",
            "stability": 3.0,
            "difficulty": 5.0,
            "fsrs_state": "review",
            "due_date": (now - timedelta(days=2)).isoformat(),
            "last_review": (now - timedelta(days=5)).isoformat(),
            "review_count": 2,
            "scheduled_days": 3,
            "elapsed_days": 5,
            "cards": {
                "id": "due-card-1",
                "topic_id": "topic-A",
                "card_type": "basic_qa",
                "question_text": "Q1",
                "answer_text": "A1",
                "question_image_url": None,
                "answer_image_url": None,
                "solution_steps": None,
                "hints": [],
                "difficulty": 0.4,
                "ege_task_number": 1,
                "topics": {"code": "ALG.LIN", "title": "Линейные"},
            },
        }
    ]

    # Cards query for new cards (seen IDs query returns empty)
    new_rows = [
        {
            "id": "new-card-1",
            "topic_id": "topic-B",
            "card_type": "basic_qa",
            "question_text": "Q2",
            "answer_text": "A2",
            "question_image_url": None,
            "answer_image_url": None,
            "solution_steps": None,
            "hints": [],
            "difficulty": 0.2,
            "ege_task_number": 2,
            "topics": {"code": "ALG.QUAD", "title": "Квадратные"},
        }
    ]

    # Chain mocking: sb.table(...).select(...).eq(...).lte(...).neq(...).execute()
    # We use a side_effect approach: first call to table("user_card_progress") for due,
    # second for seen_ids, then table("cards") for new.
    call_count = [0]

    def table_side_effect(table_name: str) -> MagicMock:
        q = MagicMock()
        q.select.return_value = q
        q.eq.return_value = q
        q.lte.return_value = q
        q.neq.return_value = q
        q.not_ = q
        q.in_.return_value = q
        q.order.return_value = q
        q.limit.return_value = q
        q.maybe_single.return_value = q

        if table_name == "user_card_progress":
            if call_count[0] == 0:
                # First call: fetch due cards
                q.execute.return_value = _mock_execute(due_rows)
            else:
                # Second call: fetch seen card IDs
                q.execute.return_value = _mock_execute([])
            call_count[0] += 1
        elif table_name == "cards":
            q.execute.return_value = _mock_execute(new_rows)

        return q

    sb.table.side_effect = table_side_effect

    generator = SessionGenerator(sb)
    cards = generator.generate(user_id="user-123", daily_goal_minutes=5)

    # Should have both due and new cards
    assert len(cards) >= 1
    card_ids = {c["card_id"] for c in cards}
    assert "due-card-1" in card_ids


def test_generator_respects_interleaving():
    """With many due cards from two topics, no topic appears > 2 in a row."""
    now = datetime.now(timezone.utc)
    sb = MagicMock()

    # Create 6 due cards: 3 from topic-A, 3 from topic-B
    def _due_row(card_id: str, topic_id: str, topic_code: str) -> dict:
        return {
            "card_id": card_id,
            "stability": 1.0,
            "difficulty": 5.0,
            "fsrs_state": "review",
            "due_date": (now - timedelta(hours=1)).isoformat(),
            "last_review": (now - timedelta(days=1)).isoformat(),
            "review_count": 1,
            "scheduled_days": 1,
            "elapsed_days": 1,
            "cards": {
                "id": card_id,
                "topic_id": topic_id,
                "card_type": "basic_qa",
                "question_text": f"Q {card_id}",
                "answer_text": "A",
                "question_image_url": None,
                "answer_image_url": None,
                "solution_steps": None,
                "hints": [],
                "difficulty": 0.5,
                "ege_task_number": 1,
                "topics": {"code": topic_code, "title": topic_code},
            },
        }

    due_rows = (
        [_due_row(f"a{i}", "topic-A", "ALG.LIN") for i in range(3)]
        + [_due_row(f"b{i}", "topic-B", "ALG.QUAD") for i in range(3)]
    )

    call_count = [0]

    def table_side_effect(table_name: str) -> MagicMock:
        q = MagicMock()
        q.select.return_value = q
        q.eq.return_value = q
        q.lte.return_value = q
        q.neq.return_value = q
        q.not_ = q
        q.in_.return_value = q
        q.order.return_value = q
        q.limit.return_value = q
        q.maybe_single.return_value = q

        if table_name == "user_card_progress":
            if call_count[0] == 0:
                q.execute.return_value = _mock_execute(due_rows)
            else:
                q.execute.return_value = _mock_execute([])
            call_count[0] += 1
        else:
            q.execute.return_value = _mock_execute([])
        return q

    sb.table.side_effect = table_side_effect

    generator = SessionGenerator(sb)
    cards = generator.generate(user_id="user-xyz", daily_goal_minutes=5)

    assert len(cards) == 6  # target for 5 min = floor(5*60/45) = 6, all 6 due cards used

    # Verify no topic > 2 consecutive
    consecutive = 1
    for i in range(1, len(cards)):
        if cards[i]["topic_id"] == cards[i - 1]["topic_id"]:
            consecutive += 1
            assert consecutive <= 2
        else:
            consecutive = 1

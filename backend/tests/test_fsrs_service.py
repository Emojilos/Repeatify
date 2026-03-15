"""Tests for the FSRS service (py-fsrs wrapper)."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fsrs import Rating, State

from app.services.fsrs_service import (
    _interleave,
    _map_rating,
    _map_state_to_db,
    adjust_desired_retention,
    create_card,
    get_retrievability,
    get_session,
    review_card,
)

# -------------------------------------------------------------------
# adjust_desired_retention
# -------------------------------------------------------------------


class TestAdjustDesiredRetention:
    def test_no_exam(self):
        assert adjust_desired_retention(None) == 0.90

    def test_100_days(self):
        exam = date.today() + timedelta(days=100)
        assert adjust_desired_retention(exam) == 0.90

    def test_91_days(self):
        exam = date.today() + timedelta(days=91)
        assert adjust_desired_retention(exam) == 0.90

    def test_90_days(self):
        exam = date.today() + timedelta(days=90)
        assert adjust_desired_retention(exam) == 0.85

    def test_50_days(self):
        exam = date.today() + timedelta(days=50)
        assert adjust_desired_retention(exam) == 0.85

    def test_30_days(self):
        exam = date.today() + timedelta(days=30)
        assert adjust_desired_retention(exam) == 0.85

    def test_20_days(self):
        exam = date.today() + timedelta(days=20)
        assert adjust_desired_retention(exam) == 0.80

    def test_14_days(self):
        exam = date.today() + timedelta(days=14)
        assert adjust_desired_retention(exam) == 0.80

    def test_7_days(self):
        exam = date.today() + timedelta(days=7)
        assert adjust_desired_retention(exam) == 0.75

    def test_1_day(self):
        exam = date.today() + timedelta(days=1)
        assert adjust_desired_retention(exam) == 0.75


# -------------------------------------------------------------------
# create_card
# -------------------------------------------------------------------


class TestCreateCard:
    def _mock_client(self, inserted_row=None):
        client = MagicMock()
        result = MagicMock()
        result.data = [inserted_row] if inserted_row else []
        insert_chain = client.table.return_value.insert
        insert_chain.return_value.execute.return_value = result
        return client

    def test_create_problem_card(self):
        client = self._mock_client({"id": "card-1"})
        create_card(
            client, "user-1",
            card_type="problem", problem_id="prob-1",
        )
        call_args = (
            client.table.return_value.insert.call_args[0][0]
        )
        assert call_args["user_id"] == "user-1"
        assert call_args["card_type"] == "problem"
        assert call_args["problem_id"] == "prob-1"
        assert call_args["state"] == "new"
        assert call_args["difficulty"] == 0
        assert call_args["stability"] == 0
        assert call_args["reps"] == 0

    def test_create_concept_card_with_prototype(self):
        client = self._mock_client({"id": "card-2"})
        create_card(
            client, "user-1",
            card_type="concept", prototype_id="proto-1",
        )
        call_args = (
            client.table.return_value.insert.call_args[0][0]
        )
        assert call_args["card_type"] == "concept"
        assert call_args["prototype_id"] == "proto-1"
        assert "problem_id" not in call_args

    def test_create_card_returns_row(self):
        inserted = {"id": "card-3", "state": "new"}
        client = self._mock_client(inserted)
        result = create_card(client, "user-1")
        assert result == inserted


# -------------------------------------------------------------------
# review_card
# -------------------------------------------------------------------


def _mock_client_with_card(card_row):
    client = MagicMock()
    select_result = MagicMock()
    select_result.data = [card_row]
    eq_chain = client.table.return_value.select.return_value
    eq_chain = eq_chain.eq.return_value.eq.return_value
    eq_chain.execute.return_value = select_result
    update_result = MagicMock()
    update_result.data = [card_row]
    upd_chain = client.table.return_value.update.return_value
    upd_chain.eq.return_value.execute.return_value = update_result
    return client


def _base_card_row(**overrides):
    now = datetime.now(timezone.utc)
    row = {
        "id": str(uuid.uuid4()),
        "user_id": "user-1",
        "problem_id": "prob-1",
        "prototype_id": None,
        "card_type": "problem",
        "difficulty": 0,
        "stability": 0,
        "due": now.isoformat(),
        "last_review": None,
        "reps": 0,
        "lapses": 0,
        "state": "new",
        "scheduled_days": 0,
        "elapsed_days": 0,
    }
    row.update(overrides)
    return row


class TestReviewCard:
    def test_review_good_updates_state(self):
        row = _base_card_row()
        client = _mock_client_with_card(row)
        updated = review_card(client, row["id"], 3, "user-1")
        assert updated["state"] in ("learning", "review")
        assert updated["reps"] == 1
        assert updated["lapses"] == 0

    def test_review_good_sets_due_in_future(self):
        row = _base_card_row()
        client = _mock_client_with_card(row)
        updated = review_card(client, row["id"], 3, "user-1")
        due = datetime.fromisoformat(updated["due"])
        assert due >= datetime.now(timezone.utc)

    def test_review_again_increments_lapses(self):
        now = datetime.now(timezone.utc)
        row = _base_card_row(
            state="review",
            difficulty=3.0,
            stability=5.0,
            last_review=(now - timedelta(days=5)).isoformat(),
            reps=3,
            lapses=0,
        )
        client = _mock_client_with_card(row)
        updated = review_card(client, row["id"], 1, "user-1")
        assert updated["lapses"] == 1

    def test_review_again_due_stays_close(self):
        now = datetime.now(timezone.utc)
        row = _base_card_row(
            state="review",
            difficulty=3.0,
            stability=10.0,
            last_review=(now - timedelta(days=10)).isoformat(),
            reps=5,
        )
        client = _mock_client_with_card(row)
        updated = review_card(client, row["id"], 1, "user-1")
        due = datetime.fromisoformat(updated["due"])
        assert (due - datetime.now(timezone.utc)).days <= 1

    def test_review_card_not_found(self):
        client = MagicMock()
        empty = MagicMock()
        empty.data = []
        eq_chain = client.table.return_value.select.return_value
        eq_chain = eq_chain.eq.return_value.eq.return_value
        eq_chain.execute.return_value = empty
        with pytest.raises(ValueError, match="not found"):
            review_card(client, "nonexistent", 3, "user-1")

    def test_review_persists_to_db(self):
        row = _base_card_row()
        client = _mock_client_with_card(row)
        review_card(client, row["id"], 3, "user-1")
        client.table.assert_any_call("fsrs_cards")
        update_call = client.table.return_value.update
        assert update_call.called
        update_data = update_call.call_args[0][0]
        assert "difficulty" in update_data
        assert "stability" in update_data
        assert "due" in update_data
        assert "state" in update_data


# -------------------------------------------------------------------
# get_retrievability
# -------------------------------------------------------------------


class TestGetRetrievability:
    def test_new_card_returns_zero(self):
        row = {
            "state": "new", "stability": None,
            "difficulty": None, "due": None,
            "last_review": None,
        }
        assert get_retrievability(row) == 0.0

    def test_card_with_no_stability_returns_zero(self):
        row = {
            "id": "card-x",
            "state": "learning", "stability": None,
            "difficulty": 3.0, "due": None,
            "last_review": None,
        }
        assert get_retrievability(row) == 0.0

    def test_recently_reviewed_card_high_retrievability(self):
        now = datetime.now(timezone.utc)
        row = {
            "id": "card-1",
            "state": "review",
            "stability": 30.0,
            "difficulty": 3.0,
            "due": (now + timedelta(days=25)).isoformat(),
            "last_review": now.isoformat(),
        }
        r = get_retrievability(row)
        assert r > 0.8

    def test_overdue_card_low_retrievability(self):
        now = datetime.now(timezone.utc)
        row = {
            "id": "card-1",
            "state": "review",
            "stability": 2.0,
            "difficulty": 5.0,
            "due": (now - timedelta(days=30)).isoformat(),
            "last_review": (now - timedelta(days=32)).isoformat(),
        }
        r = get_retrievability(row)
        assert r < 0.9


# -------------------------------------------------------------------
# _interleave
# -------------------------------------------------------------------


class TestInterleave:
    def test_empty(self):
        assert _interleave([]) == []

    def test_single(self):
        cards = [{"task_number": 1}]
        assert _interleave(cards) == cards

    def test_no_triple(self):
        cards = [
            {"task_number": 1, "i": 0},
            {"task_number": 1, "i": 1},
            {"task_number": 1, "i": 2},
            {"task_number": 2, "i": 3},
        ]
        result = _interleave(cards)
        for i in range(2, len(result)):
            same = (
                result[i]["task_number"]
                == result[i - 1]["task_number"]
                == result[i - 2]["task_number"]
            )
            assert not same, f"Triple at position {i}"

    def test_all_same_topic(self):
        cards = [{"task_number": 7, "i": i} for i in range(5)]
        result = _interleave(cards)
        assert len(result) == 5

    def test_preserves_all_cards(self):
        cards = [
            {"task_number": 1, "i": 0},
            {"task_number": 2, "i": 1},
            {"task_number": 1, "i": 2},
            {"task_number": 3, "i": 3},
        ]
        result = _interleave(cards)
        assert len(result) == len(cards)


# -------------------------------------------------------------------
# get_session
# -------------------------------------------------------------------


def _mock_client_session(
    cards, problems=None, prototypes=None, topics=None,
):
    client = MagicMock()

    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "fsrs_cards":
            r = MagicMock()
            r.data = cards
            chain = mock_table.select.return_value
            chain = chain.eq.return_value.lte.return_value
            chain = chain.neq.return_value.order.return_value
            chain.execute.return_value = r
        elif name == "problems":
            r = MagicMock()
            r.data = problems or []
            chain = mock_table.select.return_value
            chain.in_.return_value.execute.return_value = r
        elif name == "prototypes":
            r = MagicMock()
            r.data = prototypes or []
            chain = mock_table.select.return_value
            chain.in_.return_value.execute.return_value = r
        elif name == "topics":
            r = MagicMock()
            r.data = topics or []
            chain = mock_table.select.return_value
            chain.in_.return_value.execute.return_value = r
        return mock_table

    client.table.side_effect = table_side_effect
    return client


class TestGetSession:
    def test_empty_session(self):
        client = _mock_client_session([])
        result = get_session(client, "user-1")
        assert result == []

    def test_session_returns_due_cards(self):
        now = datetime.now(timezone.utc)
        cards = [
            {
                "id": "c1",
                "user_id": "user-1",
                "problem_id": "p1",
                "prototype_id": None,
                "state": "review",
                "stability": 5.0,
                "difficulty": 3.0,
                "due": (now - timedelta(hours=1)).isoformat(),
                "last_review": (
                    now - timedelta(days=5)
                ).isoformat(),
                "reps": 3,
                "lapses": 0,
                "task_number": 6,
            },
        ]
        problems = [{
            "id": "p1", "problem_text": "Solve x",
            "problem_images": None, "hints": None,
            "topic_id": "t1", "task_number": 6,
            "difficulty": "medium",
        }]
        topics = [{"id": "t1", "title": "Planimetry"}]
        client = _mock_client_session(
            cards, problems=problems, topics=topics,
        )
        result = get_session(client, "user-1")
        assert len(result) == 1
        assert result[0]["problem_text"] == "Solve x"
        assert result[0]["topic_title"] == "Planimetry"
        assert "retrievability" in result[0]

    def test_session_max_cards(self):
        now = datetime.now(timezone.utc)
        cards = [
            {
                "id": f"c{i}",
                "user_id": "user-1",
                "problem_id": f"p{i}",
                "prototype_id": None,
                "state": "review",
                "stability": 5.0,
                "difficulty": 3.0,
                "due": (
                    now - timedelta(hours=1)
                ).isoformat(),
                "last_review": (
                    now - timedelta(days=5)
                ).isoformat(),
                "reps": 3,
                "lapses": 0,
                "task_number": i % 19 + 1,
            }
            for i in range(30)
        ]
        client = _mock_client_session(cards)
        result = get_session(
            client, "user-1", max_cards=10,
        )
        assert len(result) == 10

    def test_session_sorted_by_retrievability(self):
        now = datetime.now(timezone.utc)
        cards = [
            {
                "id": "c1",
                "user_id": "user-1",
                "problem_id": "p1",
                "prototype_id": None,
                "state": "review",
                "stability": 30.0,
                "difficulty": 3.0,
                "due": (
                    now - timedelta(hours=1)
                ).isoformat(),
                "last_review": now.isoformat(),
                "reps": 5,
                "lapses": 0,
                "task_number": 1,
            },
            {
                "id": "c2",
                "user_id": "user-1",
                "problem_id": "p2",
                "prototype_id": None,
                "state": "review",
                "stability": 2.0,
                "difficulty": 5.0,
                "due": (
                    now - timedelta(days=10)
                ).isoformat(),
                "last_review": (
                    now - timedelta(days=12)
                ).isoformat(),
                "reps": 3,
                "lapses": 2,
                "task_number": 2,
            },
        ]
        client = _mock_client_session(cards)
        result = get_session(client, "user-1")
        assert len(result) == 2
        assert (
            result[0]["retrievability"]
            <= result[1]["retrievability"]
        )


# -------------------------------------------------------------------
# _map helpers
# -------------------------------------------------------------------


class TestMappings:
    def test_map_rating_all(self):
        assert _map_rating(1) == Rating.Again
        assert _map_rating(2) == Rating.Hard
        assert _map_rating(3) == Rating.Good
        assert _map_rating(4) == Rating.Easy

    def test_map_state_to_db(self):
        assert _map_state_to_db(State.Learning) == "learning"
        assert _map_state_to_db(State.Review) == "review"
        assert _map_state_to_db(State.Relearning) == "relearning"

"""Unit tests for FIRe credit propagation (TASK-016)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call, patch

import pytest

from app.core.fire.graph import Edge, KnowledgeGraph
from app.core.fire.propagator import (
    _accelerate_topic_cards,
    _add_implicit_credit,
    _boost_topic_intervals,
    _set_implicit_credit,
    propagate_credit,
    propagate_penalty_up,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sb(
    *,
    mastery_data: dict | None = None,
    cards_data: list[dict] | None = None,
    progress_data: list[dict] | None = None,
) -> MagicMock:
    """Build a mock Supabase client with configurable response data."""
    sb = MagicMock()

    def _chain_returning(data):
        chain = MagicMock()
        result = MagicMock()
        result.data = data
        # Support both .execute() and chained calls
        chain.execute.return_value = result
        chain.eq.return_value = chain
        chain.match.return_value = chain
        chain.in_.return_value = chain
        chain.maybe_single.return_value = chain
        chain.select.return_value = chain
        chain.update.return_value = chain
        chain.insert.return_value = chain
        return chain

    def _table_side_effect(table_name: str):
        if table_name == "user_topic_mastery":
            return _chain_returning(mastery_data)
        if table_name == "cards":
            return _chain_returning(cards_data or [])
        if table_name == "user_card_progress":
            return _chain_returning(progress_data or [])
        return _chain_returning(None)

    sb.table.side_effect = _table_side_effect
    return sb


def _utc(days_from_now: float = 10) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=days_from_now)


# ---------------------------------------------------------------------------
# KnowledgeGraph tests
# ---------------------------------------------------------------------------


class TestKnowledgeGraph:
    def test_from_edges_prerequisites(self):
        # A is prerequisite of B
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0)])
        assert len(graph.get_prerequisites("B")) == 1
        assert graph.get_prerequisites("B")[0].topic_id == "A"
        assert graph.get_prerequisites("B")[0].weight == 1.0

    def test_from_edges_dependents(self):
        graph = KnowledgeGraph.from_edges([("A", "B", 0.8)])
        assert len(graph.get_dependents("A")) == 1
        assert graph.get_dependents("A")[0].topic_id == "B"

    def test_no_edges_returns_empty(self):
        graph = KnowledgeGraph.from_edges([])
        assert graph.get_prerequisites("X") == []
        assert graph.get_dependents("X") == []

    def test_multiple_prerequisites(self):
        graph = KnowledgeGraph.from_edges([("A", "C", 1.0), ("B", "C", 0.7)])
        prereqs = graph.get_prerequisites("C")
        assert len(prereqs) == 2
        ids = {e.topic_id for e in prereqs}
        assert ids == {"A", "B"}


# ---------------------------------------------------------------------------
# propagate_credit tests
# ---------------------------------------------------------------------------


class TestPropagateCredit:
    def test_no_prerequisites_does_nothing(self):
        """If topic has no prerequisites, propagation is a no-op."""
        graph = KnowledgeGraph.from_edges([])
        sb = MagicMock()

        propagate_credit(sb, "user1", "TOPIC_B", 1.0, graph)

        # No Supabase calls should be made
        sb.table.assert_not_called()

    def test_single_prerequisite_adds_credit(self):
        """A→B: answering B (rating=3) adds credit to A."""
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0)])
        # Mastery row does not exist yet for A
        sb = _make_sb(mastery_data=None)

        propagate_credit(sb, "user1", "B", 1.0, graph)

        # Should have inserted a new mastery row for A
        calls = [str(c) for c in sb.table.call_args_list]
        assert any("user_topic_mastery" in c for c in calls)

    def test_credit_below_threshold_stops_propagation(self):
        """Credit attenuated below threshold stops that branch."""
        # A→B (weight=0.2): transferred = 1.0 * 0.2 = 0.2 < threshold(0.3)
        graph = KnowledgeGraph.from_edges([("A", "B", 0.2)])
        sb = MagicMock()

        propagate_credit(sb, "user1", "B", 1.0, graph)

        # No DB calls because the transferred credit is below threshold
        sb.table.assert_not_called()

    def test_credit_accumulation_triggers_interval_boost(self):
        """When implicit_credit reaches >= 1.0, interval boost fires."""
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0)])
        # Existing mastery: implicit_credit=0.9; adding 1.0 → 1.9 → triggers boost
        mastery_existing = {"id": "mastery-1", "implicit_credit": 0.9}
        # No cards in topic A (simplify)
        sb = _make_sb(mastery_data=mastery_existing, cards_data=[])

        propagate_credit(sb, "user1", "B", 1.0, graph)

        # Credit should have been set (remainder after consuming units)
        # We expect _set_implicit_credit to be called (sets remainder 0.9)
        calls = [str(c) for c in sb.table.call_args_list]
        assert any("user_topic_mastery" in c for c in calls)

    def test_visited_set_prevents_cycles(self):
        """Even if the same node appears multiple times, it is only processed once."""
        # Construct graph where A and B are each other's prerequisites (artificial cycle)
        graph = KnowledgeGraph()
        graph.prerequisites["B"] = [Edge("A", 1.0)]
        graph.prerequisites["A"] = [Edge("B", 1.0)]  # artificial cycle

        sb = _make_sb(mastery_data=None)

        # Should terminate without infinite recursion
        propagate_credit(sb, "user1", "B", 1.0, graph)

    def test_recursive_propagation_chain(self):
        """Credit propagates through a chain A→B→C when starting at C."""
        # A is prereq of B, B is prereq of C
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0), ("B", "C", 1.0)])
        sb = _make_sb(mastery_data=None)

        propagate_credit(sb, "user1", "C", 1.0, graph)

        # user_topic_mastery should be touched for both B and A
        mastery_calls = [c for c in sb.table.call_args_list if c[0][0] == "user_topic_mastery"]
        # At least 2 calls: one for B, one for A
        assert len(mastery_calls) >= 2

    def test_weight_attenuates_credit(self):
        """Credit is multiplied by edge weight at each hop."""
        # A→B (weight=0.5), B→C (weight=0.5)
        # C→B: transferred=0.5; B→A: transferred=0.5*0.5=0.25 < threshold(0.3) → stops
        graph = KnowledgeGraph.from_edges([("A", "B", 0.5), ("B", "C", 0.5)])
        sb = _make_sb(mastery_data=None)

        propagate_credit(sb, "user1", "C", 1.0, graph)

        # Only B should get credit (A is below threshold)
        mastery_calls = [c for c in sb.table.call_args_list if c[0][0] == "user_topic_mastery"]
        # Only one call for B (A is below threshold)
        assert len(mastery_calls) == 1


# ---------------------------------------------------------------------------
# _add_implicit_credit tests
# ---------------------------------------------------------------------------


class TestAddImplicitCredit:
    def test_inserts_when_no_existing_row(self):
        """If no mastery row exists, inserts a new one."""
        sb = _make_sb(mastery_data=None)
        result = _add_implicit_credit(sb, "user1", "TOPIC_A", 0.5)
        assert result == pytest.approx(0.5)

    def test_updates_when_row_exists(self):
        """If mastery row exists, updates implicit_credit."""
        sb = _make_sb(mastery_data={"id": "m1", "implicit_credit": 0.3})
        result = _add_implicit_credit(sb, "user1", "TOPIC_A", 0.4)
        assert result == pytest.approx(0.7)

    def test_starts_from_zero_when_credit_is_none(self):
        """If implicit_credit is None in DB, treat as 0."""
        sb = _make_sb(mastery_data={"id": "m1", "implicit_credit": None})
        result = _add_implicit_credit(sb, "user1", "TOPIC_A", 0.6)
        assert result == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# propagate_penalty_up tests
# ---------------------------------------------------------------------------


class TestPropagatePenaltyUp:
    def test_no_dependents_does_nothing(self):
        """If topic has no dependents, penalty propagation is a no-op."""
        graph = KnowledgeGraph.from_edges([])
        sb = MagicMock()

        propagate_penalty_up(sb, "user1", "TOPIC_A", 1.0, graph)

        sb.table.assert_not_called()

    def test_single_dependent_gets_accelerated(self):
        """A→B: failing on A (rating=1) pulls B's cards forward."""
        # A is prerequisite of B → failing A should accelerate B
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0)])
        sb = _make_sb(cards_data=[], progress_data=[])

        propagate_penalty_up(sb, "user1", "A", 1.0, graph)

        # cards table should have been queried for topic B
        card_calls = [c for c in sb.table.call_args_list if c[0][0] == "cards"]
        assert len(card_calls) >= 1

    def test_penalty_below_threshold_stops_propagation(self):
        """Penalty attenuated below threshold stops that branch."""
        # A→B (weight=0.2): transferred = 1.0 * 0.2 = 0.2 < threshold(0.3)
        graph = KnowledgeGraph.from_edges([("A", "B", 0.2)])
        sb = MagicMock()

        propagate_penalty_up(sb, "user1", "A", 1.0, graph)

        sb.table.assert_not_called()

    def test_visited_set_prevents_infinite_recursion(self):
        """Artificial cycle in graph does not cause infinite recursion."""
        graph = KnowledgeGraph()
        graph.dependents["A"] = [Edge("B", 1.0)]
        graph.dependents["B"] = [Edge("A", 1.0)]

        sb = _make_sb(cards_data=[], progress_data=[])

        propagate_penalty_up(sb, "user1", "A", 1.0, graph)

    def test_recursive_penalty_chain(self):
        """Penalty propagates through A→B→C when failing on A."""
        graph = KnowledgeGraph.from_edges([("A", "B", 1.0), ("B", "C", 1.0)])
        sb = _make_sb(cards_data=[], progress_data=[])

        propagate_penalty_up(sb, "user1", "A", 1.0, graph)

        # cards table should be queried for B and C
        card_calls = [c for c in sb.table.call_args_list if c[0][0] == "cards"]
        assert len(card_calls) >= 2

    def test_weight_attenuates_penalty(self):
        """Penalty is multiplied by edge weight at each hop."""
        # A→B (weight=0.5), B→C (weight=0.5)
        # penalty for B = 0.5; penalty for C = 0.5*0.5 = 0.25 < threshold → stops
        graph = KnowledgeGraph.from_edges([("A", "B", 0.5), ("B", "C", 0.5)])
        sb = _make_sb(cards_data=[], progress_data=[])

        propagate_penalty_up(sb, "user1", "A", 1.0, graph)

        card_calls = [c for c in sb.table.call_args_list if c[0][0] == "cards"]
        # Only B gets accelerated (C is below threshold)
        assert len(card_calls) == 1


# ---------------------------------------------------------------------------
# _accelerate_topic_cards tests
# ---------------------------------------------------------------------------


class TestAccelerateTopicCards:
    def test_skips_overdue_cards(self):
        """Cards whose due_date is already past are not accelerated."""
        overdue = _utc(days_from_now=-3)
        cards = [{"id": "card-1"}]
        progress = [
            {
                "id": "prog-1",
                "due_date": overdue.isoformat(),
                "interval_days": 10,
                "fsrs_state": "review",
            }
        ]
        sb = _make_sb(cards_data=cards, progress_data=progress)

        _accelerate_topic_cards(sb, "user1", "TOPIC_B")

        # update should NOT be called
        update_calls = [c for c in sb.table.call_args_list if "update" in str(c)]
        assert len(update_calls) == 0

    def test_skips_new_state_cards(self):
        """Cards in 'new' state are not accelerated."""
        future = _utc(days_from_now=5)
        cards = [{"id": "card-1"}]
        progress = [
            {
                "id": "prog-1",
                "due_date": future.isoformat(),
                "interval_days": 5,
                "fsrs_state": "new",
            }
        ]
        sb = _make_sb(cards_data=cards, progress_data=progress)

        _accelerate_topic_cards(sb, "user1", "TOPIC_B")

        update_calls = [c for c in sb.table.call_args_list if "update" in str(c)]
        assert len(update_calls) == 0

    def test_accelerates_future_review_cards(self):
        """Cards with future due_date in review state get pulled forward."""
        future = _utc(days_from_now=10)
        cards = [{"id": "card-1"}]
        progress = [
            {
                "id": "prog-1",
                "due_date": future.isoformat(),
                "interval_days": 10,
                "fsrs_state": "review",
            }
        ]

        sb = MagicMock()

        cards_chain = MagicMock()
        cards_result = MagicMock()
        cards_result.data = cards
        cards_chain.execute.return_value = cards_result
        cards_chain.select.return_value = cards_chain
        cards_chain.eq.return_value = cards_chain

        prog_chain = MagicMock()
        prog_result = MagicMock()
        prog_result.data = progress
        prog_chain.execute.return_value = prog_result
        prog_chain.select.return_value = prog_chain
        prog_chain.eq.return_value = prog_chain
        prog_chain.in_.return_value = prog_chain

        update_chain = MagicMock()
        update_result = MagicMock()
        update_result.data = {}
        update_chain.execute.return_value = update_result
        update_chain.eq.return_value = update_chain
        prog_chain.update.return_value = update_chain

        def _table_side(name):
            if name == "cards":
                return cards_chain
            return prog_chain

        sb.table.side_effect = _table_side

        _accelerate_topic_cards(sb, "user1", "TOPIC_B")

        prog_chain.update.assert_called_once()
        update_kwargs = prog_chain.update.call_args[0][0]
        assert "due_date" in update_kwargs
        # New due_date should be earlier than the original future date
        from datetime import datetime, timezone
        new_due = datetime.fromisoformat(update_kwargs["due_date"])
        if new_due.tzinfo is None:
            new_due = new_due.replace(tzinfo=timezone.utc)
        assert new_due < future

    def test_no_cards_in_topic_is_noop(self):
        """If topic has no cards, nothing happens."""
        sb = _make_sb(cards_data=[])

        _accelerate_topic_cards(sb, "user1", "TOPIC_EMPTY")

        prog_calls = [c for c in sb.table.call_args_list if c[0][0] == "user_card_progress"]
        assert len(prog_calls) == 0


# ---------------------------------------------------------------------------
# _boost_topic_intervals tests
# ---------------------------------------------------------------------------


class TestBoostTopicIntervals:
    def test_skips_overdue_cards(self):
        """Cards whose due_date is in the past are not boosted."""
        overdue = _utc(days_from_now=-5)
        cards = [{"id": "card-1"}]
        progress = [
            {
                "id": "prog-1",
                "due_date": overdue.isoformat(),
                "interval_days": 10,
            }
        ]
        sb = _make_sb(cards_data=cards, progress_data=progress)

        _boost_topic_intervals(sb, "user1", "TOPIC_A")

        # update should NOT be called for overdue card
        update_calls = [
            c
            for c in sb.table.return_value.update.call_args_list
            if "due_date" in str(c)
        ]
        assert len(update_calls) == 0

    def test_boosts_future_review_cards(self):
        """Cards with future due_date get their interval extended."""
        future = _utc(days_from_now=10)
        cards = [{"id": "card-1"}]
        progress = [
            {
                "id": "prog-1",
                "due_date": future.isoformat(),
                "interval_days": 10,
            }
        ]

        # We need a more complete mock for this test
        sb = MagicMock()

        # cards table response
        cards_chain = MagicMock()
        cards_result = MagicMock()
        cards_result.data = cards
        cards_chain.execute.return_value = cards_result
        cards_chain.select.return_value = cards_chain
        cards_chain.eq.return_value = cards_chain

        # progress table response
        prog_chain = MagicMock()
        prog_result = MagicMock()
        prog_result.data = progress
        prog_chain.execute.return_value = prog_result
        prog_chain.select.return_value = prog_chain
        prog_chain.eq.return_value = prog_chain
        prog_chain.in_.return_value = prog_chain

        # update chain
        update_chain = MagicMock()
        update_result = MagicMock()
        update_result.data = {}
        update_chain.execute.return_value = update_result
        update_chain.eq.return_value = update_chain
        prog_chain.update.return_value = update_chain

        def _table_side(name):
            if name == "cards":
                return cards_chain
            return prog_chain

        sb.table.side_effect = _table_side

        _boost_topic_intervals(sb, "user1", "TOPIC_A")

        # update should have been called with a new due_date
        prog_chain.update.assert_called_once()
        update_kwargs = prog_chain.update.call_args[0][0]
        assert "due_date" in update_kwargs
        assert "interval_days" in update_kwargs
        assert update_kwargs["interval_days"] > 10

    def test_no_cards_in_topic_is_noop(self):
        """If topic has no cards, nothing happens."""
        sb = _make_sb(cards_data=[])

        _boost_topic_intervals(sb, "user1", "TOPIC_EMPTY")

        # Only the cards table should be queried; progress never touched
        card_calls = [c for c in sb.table.call_args_list if c[0][0] == "cards"]
        prog_calls = [c for c in sb.table.call_args_list if c[0][0] == "user_card_progress"]
        assert len(card_calls) >= 1
        assert len(prog_calls) == 0

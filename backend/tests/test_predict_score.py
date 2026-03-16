"""Tests for predict_score service function."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.study_plan_service import (
    _POINTS,
    _primary_to_test_score,
    predict_score,
)


class TestPrimaryToTestScore:
    def test_zero(self):
        assert _primary_to_test_score(0) == 0

    def test_negative(self):
        assert _primary_to_test_score(-5) == 0

    def test_exact_5(self):
        assert _primary_to_test_score(5) == 27

    def test_exact_12(self):
        assert _primary_to_test_score(12) == 70

    def test_exact_32(self):
        assert _primary_to_test_score(32) == 100

    def test_above_max(self):
        assert _primary_to_test_score(35) == 100

    def test_interpolation_between_5_and_7(self):
        # 6 is midway between 5 (27) and 7 (40) → ~34
        result = _primary_to_test_score(6)
        assert 33 <= result <= 34

    def test_interpolation_between_12_and_18(self):
        # 15 is midway between 12 (70) and 18 (82) → ~76
        result = _primary_to_test_score(15)
        assert 75 <= result <= 77

    def test_between_0_and_5(self):
        # 3 → interpolate 0-5: 3/5 * 27 ≈ 16
        result = _primary_to_test_score(3)
        assert 15 <= result <= 17


class TestPredictScore:
    def _make_client(
        self,
        cards: list[dict],
        problems: list[dict] | None = None,
        prototypes: list[dict] | None = None,
    ) -> MagicMock:
        mock_client = MagicMock()

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "fsrs_cards":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=cards)
            elif name == "problems":
                (
                    mock_table.select.return_value
                    .in_.return_value
                    .execute.return_value
                ) = MagicMock(data=problems or [])
            elif name == "prototypes":
                (
                    mock_table.select.return_value
                    .in_.return_value
                    .execute.return_value
                ) = MagicMock(data=prototypes or [])
            return mock_table

        mock_client.table.side_effect = table_side_effect
        return mock_client

    def test_no_cards_zero_score(self):
        """No FSRS cards → predicted score is 0."""
        client = self._make_client(cards=[])

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.0,
        ):
            result = predict_score(client, "user-1")

        assert result["predicted_primary_score"] == 0
        assert result["predicted_test_score"] == 0
        assert result["breakdown"][1]["cards_count"] == 0
        assert result["breakdown"][1]["is_mastered"] is False

    def test_mastered_part1_tasks(self):
        """Tasks 1-7 with high retrievability → predicted ~7 primary."""
        cards = []
        problems = []
        for tn in range(1, 8):
            pid = f"p-{tn}"
            cards.append({
                "id": f"c-{tn}",
                "problem_id": pid,
                "prototype_id": None,
                "state": "review",
                "stability": 30.0,
                "difficulty": 3.0,
                "due": "2026-01-01T00:00:00+00:00",
                "last_review": "2026-03-15T00:00:00+00:00",
            })
            problems.append({"id": pid, "task_number": tn})

        client = self._make_client(cards=cards, problems=problems)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.95,
        ):
            result = predict_score(client, "user-1")

        assert result["predicted_primary_score"] == 7
        assert result["predicted_test_score"] == 40
        for tn in range(1, 8):
            assert result["breakdown"][tn]["is_mastered"] is True
        for tn in range(8, 13):
            assert result["breakdown"][tn]["is_mastered"] is False

    def test_mastered_all_part1(self):
        """All 12 Part 1 tasks mastered → 12 primary → 70 test."""
        cards = []
        problems = []
        for tn in range(1, 13):
            pid = f"p-{tn}"
            cards.append({
                "id": f"c-{tn}",
                "problem_id": pid,
                "prototype_id": None,
                "state": "review",
                "stability": 30.0,
                "difficulty": 3.0,
                "due": "2026-01-01T00:00:00+00:00",
                "last_review": "2026-03-15T00:00:00+00:00",
            })
            problems.append({"id": pid, "task_number": tn})

        client = self._make_client(cards=cards, problems=problems)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.9,
        ):
            result = predict_score(client, "user-1")

        assert result["predicted_primary_score"] == 12
        assert result["predicted_test_score"] == 70

    def test_part2_tasks_add_more_points(self):
        """Tasks 13, 15, 16 mastered add 2 points each."""
        cards = []
        problems = []
        for tn in list(range(1, 13)) + [13, 15, 16]:
            pid = f"p-{tn}"
            cards.append({
                "id": f"c-{tn}",
                "problem_id": pid,
                "prototype_id": None,
                "state": "review",
                "stability": 30.0,
                "difficulty": 3.0,
                "due": "2026-01-01T00:00:00+00:00",
                "last_review": "2026-03-15T00:00:00+00:00",
            })
            problems.append({"id": pid, "task_number": tn})

        client = self._make_client(cards=cards, problems=problems)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.85,
        ):
            result = predict_score(client, "user-1")

        # 12 Part1 (1 each) + 3 Part2 (2 each) = 18
        assert result["predicted_primary_score"] == 18
        assert result["predicted_test_score"] == 82

    def test_low_retrievability_not_mastered(self):
        """Cards with avg_retrievability < 0.8 are not mastered."""
        cards = [{
            "id": "c-1",
            "problem_id": "p-1",
            "prototype_id": None,
            "state": "learning",
            "stability": 1.0,
            "difficulty": 7.0,
            "due": "2026-03-16T00:00:00+00:00",
            "last_review": "2026-03-15T00:00:00+00:00",
        }]
        problems = [{"id": "p-1", "task_number": 1}]

        client = self._make_client(cards=cards, problems=problems)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.5,
        ):
            result = predict_score(client, "user-1")

        assert result["breakdown"][1]["avg_retrievability"] == 0.5
        assert result["breakdown"][1]["is_mastered"] is False
        assert result["predicted_primary_score"] == 0

    def test_prototype_cards_mapped(self):
        """Cards linked via prototype_id are mapped to correct task_number."""
        cards = [{
            "id": "c-1",
            "problem_id": None,
            "prototype_id": "proto-6",
            "state": "review",
            "stability": 30.0,
            "difficulty": 3.0,
            "due": "2026-01-01T00:00:00+00:00",
            "last_review": "2026-03-15T00:00:00+00:00",
        }]
        prototypes = [{"id": "proto-6", "task_number": 6}]

        client = self._make_client(cards=cards, prototypes=prototypes)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.9,
        ):
            result = predict_score(client, "user-1")

        assert result["breakdown"][6]["cards_count"] == 1
        assert result["breakdown"][6]["is_mastered"] is True

    def test_multiple_cards_per_task_averaged(self):
        """Multiple cards for same task → retrievability averaged."""
        cards = [
            {
                "id": "c-1",
                "problem_id": "p-1",
                "prototype_id": None,
                "state": "review",
                "stability": 30.0,
                "difficulty": 3.0,
                "due": "2026-01-01T00:00:00+00:00",
                "last_review": "2026-03-15T00:00:00+00:00",
            },
            {
                "id": "c-2",
                "problem_id": "p-2",
                "prototype_id": None,
                "state": "learning",
                "stability": 1.0,
                "difficulty": 7.0,
                "due": "2026-03-16T00:00:00+00:00",
                "last_review": "2026-03-15T00:00:00+00:00",
            },
        ]
        problems = [
            {"id": "p-1", "task_number": 7},
            {"id": "p-2", "task_number": 7},
        ]

        client = self._make_client(cards=cards, problems=problems)

        # Return different retrievabilities for the two cards
        retrievabilities = iter([0.95, 0.55])

        with patch(
            "app.services.fsrs_service.get_retrievability",
            side_effect=lambda *a, **kw: next(retrievabilities),
        ):
            result = predict_score(client, "user-1")

        assert result["breakdown"][7]["cards_count"] == 2
        assert result["breakdown"][7]["avg_retrievability"] == 0.75
        assert result["breakdown"][7]["is_mastered"] is False

    def test_boundary_retrievability_0_8(self):
        """Exactly 0.8 retrievability → mastered."""
        cards = [{
            "id": "c-1",
            "problem_id": "p-1",
            "prototype_id": None,
            "state": "review",
            "stability": 10.0,
            "difficulty": 4.0,
            "due": "2026-01-01T00:00:00+00:00",
            "last_review": "2026-03-15T00:00:00+00:00",
        }]
        problems = [{"id": "p-1", "task_number": 1}]

        client = self._make_client(cards=cards, problems=problems)

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.8,
        ):
            result = predict_score(client, "user-1")

        assert result["breakdown"][1]["is_mastered"] is True

    def test_all_19_tasks_in_breakdown(self):
        """Breakdown always contains all 19 tasks."""
        client = self._make_client(cards=[])

        with patch(
            "app.services.fsrs_service.get_retrievability",
            return_value=0.0,
        ):
            result = predict_score(client, "user-1")

        assert len(result["breakdown"]) == 19
        for tn in range(1, 20):
            assert tn in result["breakdown"]

    def test_points_match_prd_matrix(self):
        """Verify points per task match PRD 2.1."""
        for tn in range(1, 13):
            assert _POINTS[tn] == 1
        for tn in range(13, 18):
            assert _POINTS[tn] == 2
        assert _POINTS[18] == 4
        assert _POINTS[19] == 4
        # Total possible = 12 + 10 + 8 = 30... actually 12 + 5*2 + 2*4 = 30
        assert sum(_POINTS.values()) == 30

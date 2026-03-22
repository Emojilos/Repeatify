"""Tests for knowledge-map study plan service."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services.study_plan_service import (
    _mastery_status,
    _sort_by_roi,
    generate_plan,
    get_current_plan,
    get_required_tasks,
    start_assessment,
    submit_assessment,
)

# --- get_required_tasks ---


class TestGetRequiredTasks:
    def test_target_70_returns_tasks_1_to_12(self):
        tasks = get_required_tasks(70)
        assert tasks == list(range(1, 13))

    def test_target_80_includes_13_15_16(self):
        tasks = get_required_tasks(80)
        assert 13 in tasks
        assert 15 in tasks
        assert 16 in tasks
        assert 14 not in tasks

    def test_target_90_includes_14_17(self):
        tasks = get_required_tasks(90)
        assert 14 in tasks
        assert 17 in tasks

    def test_target_100_all_19(self):
        tasks = get_required_tasks(100)
        assert tasks == list(range(1, 20))


# --- _mastery_status ---


class TestMasteryStatus:
    def test_zero_total(self):
        assert _mastery_status(0, 0) == "not_tested"

    def test_weak(self):
        assert _mastery_status(0, 10) == "weak"
        assert _mastery_status(3, 10) == "weak"

    def test_medium(self):
        assert _mastery_status(4, 10) == "medium"
        assert _mastery_status(6, 10) == "medium"

    def test_good(self):
        assert _mastery_status(7, 10) == "good"
        assert _mastery_status(9, 10) == "good"

    def test_mastered(self):
        assert _mastery_status(10, 10) == "mastered"


# --- _sort_by_roi ---


class TestSortByROI:
    def test_part1_roi_order(self):
        tasks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        result = _sort_by_roi(tasks)
        assert result == [7, 6, 4, 8, 1, 2, 12, 9, 3, 5, 10, 11]

    def test_subset(self):
        tasks = [3, 7, 12]
        result = _sort_by_roi(tasks)
        assert result == [7, 12, 3]

    def test_with_part2_appended(self):
        tasks = [7, 6, 13, 15]
        result = _sort_by_roi(tasks)
        assert result[0] == 7
        assert result[1] == 6
        assert 13 in result[2:]
        assert 15 in result[2:]


# --- generate_plan ---


def _mock_client(assessments=None):
    """Create a mock Supabase client for plan generation."""
    client = MagicMock()

    # Mock task_assessments query
    assess_result = MagicMock()
    assess_result.data = assessments or []

    # Mock the chained calls for task_assessments
    def table_side_effect(name):
        mock_table = MagicMock()
        if name == "task_assessments":
            (
                mock_table.select.return_value
                .eq.return_value
                .order.return_value
                .execute.return_value
            ) = assess_result
        return mock_table

    client.table.side_effect = table_side_effect

    return client


class TestGeneratePlan:
    def test_target_70_no_assessments(self):
        client = _mock_client()
        result = generate_plan(client, "user-1", 70)
        plan = result["plan_data"]
        assert plan["target_score"] == 70
        tasks = plan["tasks"]
        assert len(tasks) == 12
        assert all(t["status"] == "not_tested" for t in tasks)

    def test_target_80_includes_part2(self):
        client = _mock_client()
        result = generate_plan(client, "user-1", 80)
        plan = result["plan_data"]
        task_numbers = [t["task_number"] for t in plan["tasks"]]
        assert 13 in task_numbers
        assert 15 in task_numbers
        assert 16 in task_numbers

    def test_with_assessments(self):
        assessments = [
            {"task_number": 7, "correct_count": 10, "total_count": 10, "assessed_at": "2026-03-22T00:00:00Z"},
            {"task_number": 1, "correct_count": 3, "total_count": 10, "assessed_at": "2026-03-22T00:00:00Z"},
        ]
        client = _mock_client(assessments)
        result = generate_plan(client, "user-1", 70)
        plan = result["plan_data"]

        task7 = next(t for t in plan["tasks"] if t["task_number"] == 7)
        assert task7["status"] == "mastered"
        assert task7["correct"] == 10

        task1 = next(t for t in plan["tasks"] if t["task_number"] == 1)
        assert task1["status"] == "weak"
        assert task1["correct"] == 3

    def test_plan_persisted(self):
        client = _mock_client()
        result = generate_plan(client, "user-1", 70)
        assert result["is_active"] is True
        assert result["id"]
        client.table.assert_any_call("user_study_plan")

    def test_target_100_all_tasks(self):
        client = _mock_client()
        result = generate_plan(client, "user-1", 100)
        plan = result["plan_data"]
        assert len(plan["tasks"]) == 19


# --- start_assessment ---


class TestStartAssessment:
    def test_returns_problems(self):
        client = MagicMock()
        problems = [
            {"id": f"p{i}", "task_number": 1, "difficulty": "medium",
             "problem_text": f"Problem {i}", "problem_images": None, "hints": None}
            for i in range(15)
        ]
        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=problems)

        result = start_assessment(client, "user-1", 1)
        assert len(result) == 10
        # Should not include correct_answer
        for p in result:
            assert "correct_answer" not in p

    def test_fewer_than_10_problems(self):
        client = MagicMock()
        problems = [
            {"id": f"p{i}", "task_number": 1, "difficulty": "medium",
             "problem_text": f"Problem {i}", "problem_images": None, "hints": None}
            for i in range(5)
        ]
        (
            client.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
        ) = MagicMock(data=problems)

        result = start_assessment(client, "user-1", 1)
        assert len(result) == 5


# --- submit_assessment ---


class TestSubmitAssessment:
    def test_grades_correctly(self):
        client = MagicMock()

        # Mock problems table
        problems_data = [
            {"id": "p1", "correct_answer": "42", "answer_tolerance": 0, "solution_markdown": None},
            {"id": "p2", "correct_answer": "7", "answer_tolerance": 0, "solution_markdown": None},
            {"id": "p3", "correct_answer": "100", "answer_tolerance": 0, "solution_markdown": None},
        ]

        def table_side_effect(name):
            mock_table = MagicMock()
            if name == "problems":
                (
                    mock_table.select.return_value
                    .in_.return_value
                    .execute.return_value
                ) = MagicMock(data=problems_data)
            elif name == "task_assessments":
                mock_table.insert.return_value.execute.return_value = MagicMock()
            elif name == "fsrs_cards":
                (
                    mock_table.select.return_value
                    .eq.return_value
                    .eq.return_value
                    .execute.return_value
                ) = MagicMock(data=[])
                mock_table.insert.return_value.execute.return_value = MagicMock()
            return mock_table

        client.table.side_effect = table_side_effect

        answers = [
            {"problem_id": "p1", "answer": "42"},
            {"problem_id": "p2", "answer": "8"},   # wrong
            {"problem_id": "p3", "answer": "100"},
        ]

        result = submit_assessment(client, "user-1", 1, answers)
        assert result["correct_count"] == 2
        assert result["total_count"] == 3
        assert result["status"] == "weak"
        assert len(result["details"]) == 3
        assert result["details"][0]["is_correct"] is True
        assert result["details"][1]["is_correct"] is False
        assert result["details"][2]["is_correct"] is True


# --- get_current_plan ---


class TestGetCurrentPlan:
    def test_returns_plan(self):
        client = MagicMock()
        plan_row = {
            "id": "plan-1",
            "user_id": "user-1",
            "is_active": True,
            "plan_data": {},
        }
        result_mock = MagicMock()
        result_mock.data = [plan_row]
        chain = (
            client.table.return_value.select.return_value
            .eq.return_value.eq.return_value
            .order.return_value.limit.return_value
        )
        chain.execute.return_value = result_mock
        assert get_current_plan(client, "user-1") == plan_row

    def test_returns_none_when_no_plan(self):
        client = MagicMock()
        result_mock = MagicMock()
        result_mock.data = []
        chain = (
            client.table.return_value.select.return_value
            .eq.return_value.eq.return_value
            .order.return_value.limit.return_value
        )
        chain.execute.return_value = result_mock
        assert get_current_plan(client, "user-1") is None

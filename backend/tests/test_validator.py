"""Tests for Shkolkovo parsed problem validation."""

from __future__ import annotations

from scripts.shkolkovo_parser.problem_parser import ParsedProblem
from scripts.shkolkovo_parser.validator import (
    INVALID_TASK_NUMBER,
    MISSING_CORRECT_ANSWER,
    MISSING_PROBLEM_TEXT,
    ProblemValidationError,
    ProblemValidationResult,
    ValidatedProblemRecord,
    validate_problem,
)


def test_validator_marks_complete_record_as_ok() -> None:
    problem = ParsedProblem(
        problem_text="Найдите гипотенузу.",
        correct_answer="13",
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
        source_id="100601",
    )

    result = validate_problem(
        problem,
        task_number=6,
        category="Планиметрия",
        subcategory="Треугольники",
    )

    assert result == ProblemValidationResult(
        record=ValidatedProblemRecord(
            task_number=6,
            problem_text="Найдите гипотенузу.",
            correct_answer="13",
            source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
            source_id="100601",
            category="Планиметрия",
            subcategory="Треугольники",
            parse_status="ok",
            parse_errors=(),
        ),
        error=None,
    )
    assert result.is_usable is True
    assert result.record is not None
    assert result.record.to_dataset_record()["parse_errors"] == []


def test_validator_marks_usable_problem_without_answer_as_partial() -> None:
    problem = ParsedProblem(
        problem_text="Катеты равны 5 и 12. Найдите гипотенузу.",
        correct_answer=None,
        source_url="https://3.shkolkovo.online/problem/100602?SubjectId=1",
        source_id="100602",
    )

    result = validate_problem(problem, task_number=6)

    assert result.error is None
    assert result.record is not None
    assert result.record.parse_status == "partial"
    assert result.record.parse_errors == (MISSING_CORRECT_ANSWER,)
    assert result.record.correct_answer is None


def test_validator_sends_missing_problem_text_to_errors_file_record() -> None:
    problem = ParsedProblem(
        problem_text="  ",
        correct_answer="42",
        source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
        source_id="100603",
    )

    result = validate_problem(problem, task_number=6)

    assert result.record is None
    assert result.is_usable is False
    assert result.error == ProblemValidationError(
        task_number=6,
        source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
        source_id="100603",
        parse_errors=(MISSING_PROBLEM_TEXT,),
        message="problem page has no usable problem text",
    )
    assert result.error is not None
    assert result.error.to_error_record() == {
        "task_number": 6,
        "source_url": "https://3.shkolkovo.online/problem/100603?SubjectId=1",
        "source_id": "100603",
        "parse_errors": [MISSING_PROBLEM_TEXT],
        "message": "problem page has no usable problem text",
    }


def test_validator_rejects_invalid_task_number() -> None:
    problem = ParsedProblem(
        problem_text="Найдите значение выражения.",
        correct_answer="42",
        source_url="https://3.shkolkovo.online/problem/100604?SubjectId=1",
        source_id="100604",
    )

    result = validate_problem(problem, task_number=20)

    assert result.record is None
    assert result.error is not None
    assert result.error.parse_errors == (INVALID_TASK_NUMBER,)

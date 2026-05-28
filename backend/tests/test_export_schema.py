"""Tests for Shkolkovo parser JSON export schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from scripts.shkolkovo_parser.exporter import (
    ExportResult,
    build_dataset_record,
    build_error_record,
    content_hash_for_problem,
    export_task_files,
)
from scripts.shkolkovo_parser.validator import (
    MISSING_CORRECT_ANSWER,
    MISSING_PROBLEM_TEXT,
    ParseStatus,
    ProblemValidationError,
    ValidatedProblemRecord,
)


def _validated_record(
    *,
    correct_answer: str | None = "10",
    parse_status: str = "ok",
    parse_errors: tuple[str, ...] = (),
) -> ValidatedProblemRecord:
    return ValidatedProblemRecord(
        task_number=6,
        problem_text="В треугольнике ABC найдите AB.",
        correct_answer=correct_answer,
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
        source_id="100601",
        category="Планиметрия",
        subcategory="Треугольники",
        parse_status=cast(ParseStatus, parse_status),
        parse_errors=parse_errors,
    )


def test_build_dataset_record_contains_required_prd_fields() -> None:
    record = build_dataset_record(_validated_record())

    assert record == {
        "task_number": 6,
        "category": "Планиметрия",
        "subcategory": "Треугольники",
        "problem_text": "В треугольнике ABC найдите AB.",
        "correct_answer": "10",
        "difficulty": "medium",
        "answer_tolerance": 0,
        "solution_markdown": None,
        "hints": [],
        "problem_images": [],
        "solution_images": [],
        "source_image_urls": [],
        "source": "shkolkovo",
        "source_id": "100601",
        "source_url": "https://3.shkolkovo.online/problem/100601?SubjectId=1",
        "content_hash": content_hash_for_problem(
            task_number=6,
            problem_text="В треугольнике ABC найдите AB.",
        ),
        "parse_status": "ok",
        "parse_errors": [],
    }
    assert len(record["content_hash"]) == 64


def test_build_dataset_record_keeps_mvp_solution_fields_empty() -> None:
    record = build_dataset_record(
        _validated_record(
            correct_answer=None,
            parse_status="partial",
            parse_errors=(MISSING_CORRECT_ANSWER,),
        ),
    )

    assert record["correct_answer"] is None
    assert record["solution_markdown"] is None
    assert record["hints"] == []
    assert record["solution_images"] == []
    assert record["parse_status"] == "partial"
    assert record["parse_errors"] == [MISSING_CORRECT_ANSWER]


def test_build_error_record_contains_page_without_usable_problem_text() -> None:
    error = ProblemValidationError(
        task_number=6,
        source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
        source_id="100603",
        parse_errors=(MISSING_PROBLEM_TEXT,),
        message="problem page has no usable problem text",
    )

    assert build_error_record(error) == {
        "task_number": 6,
        "source_url": "https://3.shkolkovo.online/problem/100603?SubjectId=1",
        "source_id": "100603",
        "error": MISSING_PROBLEM_TEXT,
        "details": "problem page has no usable problem text",
        "parse_errors": [MISSING_PROBLEM_TEXT],
    }


def test_export_task_files_writes_valid_json_arrays_for_task_number(
    tmp_path: Path,
) -> None:
    error = ProblemValidationError(
        task_number=6,
        source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
        source_id="100603",
        parse_errors=(MISSING_PROBLEM_TEXT,),
        message="problem page has no usable problem text",
    )

    result = export_task_files(
        task_number=6,
        records=(_validated_record(),),
        errors=(error,),
        output_dir=tmp_path,
    )

    assert result == ExportResult(
        task_number=6,
        output_file=tmp_path / "task_6.json",
        errors_file=tmp_path / "task_6_errors.json",
        records_written=1,
        errors_written=1,
    )
    task_records = json.loads(result.output_file.read_text(encoding="utf-8"))
    error_records = json.loads(result.errors_file.read_text(encoding="utf-8"))
    assert isinstance(task_records, list)
    assert isinstance(error_records, list)
    assert task_records[0]["task_number"] == 6
    assert task_records[0]["solution_markdown"] is None
    assert task_records[0]["hints"] == []
    assert task_records[0]["solution_images"] == []
    assert error_records[0]["error"] == MISSING_PROBLEM_TEXT

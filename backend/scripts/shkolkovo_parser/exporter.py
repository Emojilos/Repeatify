"""Export validated Shkolkovo parser records to JSON files."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.shkolkovo_parser.catalog_parser import MAX_TASK_NUMBER, MIN_TASK_NUMBER
from scripts.shkolkovo_parser.config import shkolkovo_data_dir
from scripts.shkolkovo_parser.validator import (
    ProblemValidationError,
    ValidatedProblemRecord,
)

DEFAULT_DIFFICULTY = "medium"
DEFAULT_SOURCE = "shkolkovo"


@dataclass(frozen=True)
class ExportResult:
    """Paths written by a task export."""

    task_number: int
    output_file: Path
    errors_file: Path
    records_written: int
    errors_written: int


def export_task_files(
    *,
    task_number: int,
    records: list[ValidatedProblemRecord] | tuple[ValidatedProblemRecord, ...],
    errors: list[ProblemValidationError] | tuple[ProblemValidationError, ...] = (),
    output_dir: Path | None = None,
) -> ExportResult:
    """Write task_N.json and task_N_errors.json for one task number."""
    _validate_task_number(task_number)
    task_records = [build_dataset_record(record) for record in records]
    error_records = [build_error_record(error) for error in errors]

    target_dir = output_dir or shkolkovo_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / task_filename(task_number)
    errors_file = target_dir / task_errors_filename(task_number)

    _write_json_array(output_file, task_records)
    _write_json_array(errors_file, error_records)

    return ExportResult(
        task_number=task_number,
        output_file=output_file,
        errors_file=errors_file,
        records_written=len(task_records),
        errors_written=len(error_records),
    )


def build_dataset_record(
    record: ValidatedProblemRecord,
    *,
    problem_images: list[str] | tuple[str, ...] = (),
    source_image_urls: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    """Return a JSON-ready task_N.json record with the MVP schema."""
    return {
        "task_number": record.task_number,
        "category": record.category,
        "subcategory": record.subcategory,
        "problem_text": record.problem_text,
        "correct_answer": record.correct_answer,
        "difficulty": DEFAULT_DIFFICULTY,
        "answer_tolerance": 0,
        "solution_markdown": None,
        "hints": [],
        "problem_images": list(problem_images),
        "solution_images": [],
        "source_image_urls": list(source_image_urls),
        "source": DEFAULT_SOURCE,
        "source_id": record.source_id,
        "source_url": record.source_url,
        "content_hash": content_hash_for_problem(
            task_number=record.task_number,
            problem_text=record.problem_text,
        ),
        "parse_status": record.parse_status,
        "parse_errors": list(record.parse_errors),
    }


def build_error_record(error: ProblemValidationError) -> dict[str, Any]:
    """Return a JSON-ready task_N_errors.json record."""
    parse_errors = list(error.parse_errors)
    return {
        "task_number": error.task_number,
        "source_url": error.source_url,
        "source_id": error.source_id,
        "error": parse_errors[0] if parse_errors else "unknown_error",
        "details": error.message,
        "parse_errors": parse_errors,
    }


def content_hash_for_problem(*, task_number: int, problem_text: str) -> str:
    """Return the stable SHA-256 identity used by the export schema."""
    payload = f"{task_number}\n{problem_text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def task_filename(task_number: int) -> str:
    """Return the main dataset filename for a task number."""
    _validate_task_number(task_number)
    return f"task_{task_number}.json"


def task_errors_filename(task_number: int) -> str:
    """Return the errors filename for a task number."""
    _validate_task_number(task_number)
    return f"task_{task_number}_errors.json"


def _write_json_array(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _validate_task_number(task_number: int) -> None:
    if MIN_TASK_NUMBER <= task_number <= MAX_TASK_NUMBER:
        return
    msg = f"task_number must be between {MIN_TASK_NUMBER} and {MAX_TASK_NUMBER}"
    raise ValueError(msg)

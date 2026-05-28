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
    duplicates_skipped: int = 0


def export_task_files(
    *,
    task_number: int,
    records: list[ValidatedProblemRecord] | tuple[ValidatedProblemRecord, ...],
    errors: list[ProblemValidationError] | tuple[ProblemValidationError, ...] = (),
    output_dir: Path | None = None,
) -> ExportResult:
    """Write task_N.json and task_N_errors.json for one task number."""
    _validate_task_number(task_number)
    target_dir = output_dir or shkolkovo_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_file = target_dir / task_filename(task_number)
    errors_file = target_dir / task_errors_filename(task_number)

    existing_task_records = _read_json_array(output_file)
    new_task_records = [build_dataset_record(record) for record in records]
    task_records, duplicates_skipped = _merge_unique_records(
        existing_task_records=existing_task_records,
        new_task_records=new_task_records,
    )
    error_records = [build_error_record(error) for error in errors]

    _write_json_array(output_file, task_records)
    _write_json_array(errors_file, error_records)

    return ExportResult(
        task_number=task_number,
        output_file=output_file,
        errors_file=errors_file,
        records_written=len(task_records),
        errors_written=len(error_records),
        duplicates_skipped=duplicates_skipped,
    )


def build_dataset_record(
    record: ValidatedProblemRecord,
    *,
    problem_images: list[str] | tuple[str, ...] | None = None,
    source_image_urls: list[str] | tuple[str, ...] | None = None,
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
        "problem_images": list(
            record.problem_images if problem_images is None else problem_images,
        ),
        "solution_images": [],
        "source_image_urls": list(
            record.source_image_urls
            if source_image_urls is None
            else source_image_urls,
        ),
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
    """Return SHA-256 identity from task number and normalized problem text."""
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


def _read_json_array(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    raw_records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_records, list):
        msg = f"{path} must contain a JSON array"
        raise ValueError(msg)

    records: list[dict[str, Any]] = []
    for raw_record in raw_records:
        if not isinstance(raw_record, dict):
            msg = f"{path} must contain only JSON objects"
            raise ValueError(msg)
        records.append(raw_record)
    return records


def _merge_unique_records(
    *,
    existing_task_records: list[dict[str, Any]],
    new_task_records: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    records = list(existing_task_records)
    seen_hashes = _record_hashes(existing_task_records)
    duplicates_skipped = 0

    for record in new_task_records:
        content_hash = record.get("content_hash")
        if isinstance(content_hash, str) and content_hash in seen_hashes:
            duplicates_skipped += 1
            continue

        records.append(record)
        if isinstance(content_hash, str):
            seen_hashes.add(content_hash)

    return records, duplicates_skipped


def _record_hashes(records: list[dict[str, Any]]) -> set[str]:
    return {
        content_hash
        for record in records
        if isinstance(content_hash := record.get("content_hash"), str)
    }


def _validate_task_number(task_number: int) -> None:
    if MIN_TASK_NUMBER <= task_number <= MAX_TASK_NUMBER:
        return
    msg = f"task_number must be between {MIN_TASK_NUMBER} and {MAX_TASK_NUMBER}"
    raise ValueError(msg)

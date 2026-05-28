"""Write per-task Shkolkovo parser run reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.shkolkovo_parser.config import repository_root, shkolkovo_data_dir
from scripts.shkolkovo_parser.exporter import ExportResult
from scripts.shkolkovo_parser.validator import (
    IMAGE_DOWNLOAD_FAILED,
    ValidatedProblemRecord,
)


@dataclass(frozen=True)
class TaskRunReport:
    """Counters and files produced by one task-number parser run."""

    task_number: int
    started_at: datetime
    finished_at: datetime
    pages_visited: int
    links_found: int
    parsed_ok: int
    parsed_partial: int
    duplicates_skipped: int
    skipped: int
    images_downloaded: int
    images_failed: int
    output_file: Path
    errors_file: Path


@dataclass(frozen=True)
class ReportResult:
    """Path and JSON payload written for a task report."""

    report_file: Path
    report: dict[str, Any]


def write_task_report(
    *,
    task_number: int,
    started_at: datetime,
    finished_at: datetime,
    pages_visited: int,
    links_found: int,
    records: tuple[ValidatedProblemRecord, ...],
    export: ExportResult,
    skipped: int,
    output_dir: Path | None = None,
) -> ReportResult:
    """Write task_N_report.json for one parser run."""
    target_dir = output_dir or shkolkovo_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    report_file = target_dir / task_report_filename(task_number)
    report = build_task_report(
        TaskRunReport(
            task_number=task_number,
            started_at=started_at,
            finished_at=finished_at,
            pages_visited=pages_visited,
            links_found=links_found,
            parsed_ok=sum(record.parse_status == "ok" for record in records),
            parsed_partial=sum(
                record.parse_status == "partial" for record in records
            ),
            duplicates_skipped=export.duplicates_skipped,
            skipped=skipped,
            images_downloaded=sum(len(record.problem_images) for record in records),
            images_failed=sum(_image_failures(record) for record in records),
            output_file=export.output_file,
            errors_file=export.errors_file,
        ),
    )
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return ReportResult(report_file=report_file, report=report)


def build_task_report(report: TaskRunReport) -> dict[str, Any]:
    """Return a JSON-ready task_N_report.json payload."""
    return {
        "task_number": report.task_number,
        "started_at": _format_timestamp(report.started_at),
        "finished_at": _format_timestamp(report.finished_at),
        "pages_visited": report.pages_visited,
        "links_found": report.links_found,
        "parsed_ok": report.parsed_ok,
        "parsed_partial": report.parsed_partial,
        "duplicates_skipped": report.duplicates_skipped,
        "skipped": report.skipped,
        "images_downloaded": report.images_downloaded,
        "images_failed": report.images_failed,
        "output_file": _repo_relative_path(report.output_file),
        "errors_file": _repo_relative_path(report.errors_file),
    }


def task_report_filename(task_number: int) -> str:
    """Return the report filename for a task number."""
    return f"task_{task_number}_report.json"


def _image_failures(record: ValidatedProblemRecord) -> int:
    return sum(
        parse_error.startswith(f"{IMAGE_DOWNLOAD_FAILED}:")
        for parse_error in record.parse_errors
    )


def _format_timestamp(value: datetime) -> str:
    timestamp = value
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _repo_relative_path(path: Path) -> str:
    resolved_path = path.resolve()
    try:
        return resolved_path.relative_to(repository_root()).as_posix()
    except ValueError:
        return resolved_path.as_posix()

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
    status: str = "completed"
    critical_errors: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True)
class ReportResult:
    """Path and JSON payload written for a task report."""

    report_file: Path
    report: dict[str, Any]


@dataclass(frozen=True)
class RunReportResult:
    """Path and JSON payload written for an aggregate parser run report."""

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
    status: str = "completed",
    critical_errors: tuple[dict[str, Any], ...] = (),
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
            status=status,
            critical_errors=critical_errors,
        ),
    )
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return ReportResult(report_file=report_file, report=report)


def write_run_report(
    *,
    started_at: datetime,
    finished_at: datetime,
    mode: str,
    parameters: dict[str, Any],
    task_reports: tuple[ReportResult, ...],
    critical_errors: tuple[dict[str, Any], ...] = (),
    output_dir: Path | None = None,
) -> RunReportResult:
    """Write run_report_YYYYMMDD_HHMMSS.json for an aggregate run."""
    target_dir = output_dir or shkolkovo_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    report_file = target_dir / run_report_filename(started_at)
    report = build_run_report(
        started_at=started_at,
        finished_at=finished_at,
        mode=mode,
        parameters=parameters,
        task_reports=task_reports,
        critical_errors=critical_errors,
    )
    report_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return RunReportResult(report_file=report_file, report=report)


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
        "status": report.status,
        "critical_errors": list(report.critical_errors),
    }


def build_run_report(
    *,
    started_at: datetime,
    finished_at: datetime,
    mode: str,
    parameters: dict[str, Any],
    task_reports: tuple[ReportResult, ...],
    critical_errors: tuple[dict[str, Any], ...] = (),
) -> dict[str, Any]:
    """Return a JSON-ready aggregate run report payload."""
    reports = [report.report for report in task_reports]
    return {
        "started_at": _format_timestamp(started_at),
        "finished_at": _format_timestamp(finished_at),
        "mode": mode,
        "parameters": parameters,
        "totals": {
            "tasks_processed": len(reports),
            "pages_visited": sum(report["pages_visited"] for report in reports),
            "links_found": sum(report["links_found"] for report in reports),
            "parsed_ok": sum(report["parsed_ok"] for report in reports),
            "parsed_partial": sum(
                report["parsed_partial"] for report in reports
            ),
            "duplicates_skipped": sum(
                report["duplicates_skipped"] for report in reports
            ),
            "skipped": sum(report["skipped"] for report in reports),
            "images_downloaded": sum(
                report["images_downloaded"] for report in reports
            ),
            "images_failed": sum(report["images_failed"] for report in reports),
        },
        "tasks": [
            {
                "task_number": report["task_number"],
                "report_file": _repo_relative_path(result.report_file),
                "output_file": report["output_file"],
                "errors_file": report["errors_file"],
            }
            for result, report in zip(task_reports, reports, strict=True)
        ],
        "partial_records": _partial_review_records(reports),
        "failed_records": _failed_review_records(reports),
        "critical_errors": list(critical_errors),
    }


def task_report_filename(task_number: int) -> str:
    """Return the report filename for a task number."""
    return f"task_{task_number}_report.json"


def run_report_filename(started_at: datetime) -> str:
    """Return the aggregate report filename for a parser run."""
    timestamp = started_at.astimezone(UTC).strftime("%Y%m%d_%H%M%S")
    return f"run_report_{timestamp}.json"


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


def _partial_review_records(
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    partial_records: list[dict[str, Any]] = []
    for report in reports:
        for record in _read_report_json_array(report["output_file"]):
            if record.get("parse_status") != "partial":
                continue
            partial_records.append(
                {
                    "task_number": record.get("task_number"),
                    "source_id": record.get("source_id"),
                    "source_url": record.get("source_url"),
                    "parse_status": record.get("parse_status"),
                    "parse_errors": record.get("parse_errors", []),
                },
            )
    return partial_records


def _failed_review_records(
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failed_records: list[dict[str, Any]] = []
    for report in reports:
        for record in _read_report_json_array(report["errors_file"]):
            failed_records.append(
                {
                    "task_number": record.get("task_number"),
                    "source_id": record.get("source_id"),
                    "source_url": record.get("source_url"),
                    "error": record.get("error"),
                    "parse_errors": record.get("parse_errors", []),
                    "details": record.get("details"),
                },
            )
    return failed_records


def _read_report_json_array(path_value: Any) -> list[dict[str, Any]]:
    path = Path(str(path_value))
    if not path.is_absolute():
        path = repository_root() / path

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

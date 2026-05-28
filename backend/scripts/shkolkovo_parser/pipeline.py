"""Offline pipeline assembly for Shkolkovo parser test runs."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.shkolkovo_parser.catalog_parser import ParsedCatalog, parse_catalog_html
from scripts.shkolkovo_parser.config import repository_root
from scripts.shkolkovo_parser.debug import DebugArtifactResult, write_debug_artifacts
from scripts.shkolkovo_parser.exporter import ExportResult, export_task_files
from scripts.shkolkovo_parser.problem_parser import parse_problem_html
from scripts.shkolkovo_parser.reporter import (
    ReportResult,
    RunReportResult,
    write_run_report,
    write_task_report,
)
from scripts.shkolkovo_parser.validator import (
    ProblemValidationError,
    ValidatedProblemRecord,
    validate_problem,
)

DEFAULT_TEST_TASK_NUMBER = 6
MISSING_OFFLINE_SNAPSHOT = "missing_offline_snapshot"
ProgressReporter = Callable[[str], None]


@dataclass(frozen=True)
class OfflinePipelineResult:
    """Files and counters produced by one offline task pipeline run."""

    task_number: int
    export: ExportResult
    records: tuple[ValidatedProblemRecord, ...]
    errors: tuple[ProblemValidationError, ...]
    catalog_links_found: int
    pages_visited: int
    skipped: int
    report: ReportResult
    debug: DebugArtifactResult | None = None

    @property
    def duplicates_skipped(self) -> int:
        """Number of dataset records skipped because they already existed."""
        return self.export.duplicates_skipped


@dataclass(frozen=True)
class OfflineAllPipelineResult:
    """Files and counters produced by an aggregate offline pipeline run."""

    task_results: tuple[OfflinePipelineResult, ...]
    run_report: RunReportResult

    @property
    def task_numbers(self) -> tuple[int, ...]:
        """Task numbers processed by this aggregate run."""
        return tuple(result.task_number for result in self.task_results)


def run_fixture_pipeline(
    *,
    task_number: int = DEFAULT_TEST_TASK_NUMBER,
    per_subcategory: int | None = None,
    fixture_dir: Path | None = None,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    debug: bool = False,
) -> OfflinePipelineResult:
    """Run the parser pipeline on bundled local HTML fixtures."""
    fixture_dir = fixture_dir or default_fixture_dir()
    catalog_html = (fixture_dir / "catalog_task_6.html").read_text(
        encoding="utf-8",
    )
    problem_pages = load_problem_fixture_pages(fixture_dir)
    return run_offline_pipeline(
        catalog_html=catalog_html,
        problem_pages=problem_pages,
        task_number=task_number,
        per_subcategory=per_subcategory,
        output_dir=output_dir,
        progress=progress,
        debug=debug,
    )


def run_all_fixture_pipeline(
    *,
    per_subcategory: int | None = None,
    fixture_dir: Path | None = None,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    parameters: dict[str, object] | None = None,
    debug: bool = False,
) -> OfflineAllPipelineResult:
    """Run the offline pipeline for every task number found in fixtures."""
    fixture_dir = fixture_dir or default_fixture_dir()
    catalog_html = (fixture_dir / "catalog_task_6.html").read_text(
        encoding="utf-8",
    )
    problem_pages = load_problem_fixture_pages(fixture_dir)
    return run_all_offline_pipeline(
        catalog_html=catalog_html,
        problem_pages=problem_pages,
        per_subcategory=per_subcategory,
        output_dir=output_dir,
        progress=progress,
        parameters=parameters,
        debug=debug,
    )


def run_all_offline_pipeline(
    *,
    catalog_html: str,
    problem_pages: dict[str, str],
    per_subcategory: int | None = None,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    parameters: dict[str, object] | None = None,
    debug: bool = False,
) -> OfflineAllPipelineResult:
    """Parse saved catalog/problem HTML for all discovered task numbers."""
    started_at = datetime.now(UTC)
    catalog = parse_catalog_html(catalog_html)
    task_numbers = _discovered_task_numbers(catalog)
    _report_progress(
        progress,
        "All mode: discovered task numbers "
        f"{', '.join(str(number) for number in task_numbers)}.",
    )

    task_results = tuple(
        run_offline_pipeline(
            catalog_html=catalog_html,
            problem_pages=problem_pages,
            task_number=task_number,
            per_subcategory=per_subcategory,
            output_dir=output_dir,
            progress=progress,
            debug=debug,
        )
        for task_number in task_numbers
    )
    run_report = write_run_report(
        started_at=started_at,
        finished_at=datetime.now(UTC),
        mode="all",
        parameters=parameters or {},
        task_reports=tuple(result.report for result in task_results),
        output_dir=output_dir,
    )
    return OfflineAllPipelineResult(
        task_results=task_results,
        run_report=run_report,
    )


def run_offline_pipeline(
    *,
    catalog_html: str,
    problem_pages: dict[str, str],
    task_number: int,
    per_subcategory: int | None = None,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    debug: bool = False,
) -> OfflinePipelineResult:
    """Parse saved catalog/problem HTML and export one task dataset."""
    started_at = datetime.now(UTC)
    catalog = parse_catalog_html(catalog_html)
    _report_progress(
        progress,
        f"Task {task_number}: found {len(catalog.problems)} catalog links.",
    )
    records: list[ValidatedProblemRecord] = []
    errors: list[ProblemValidationError] = []
    subcategory_counts: dict[tuple[int, str | None, str | None], int] = {}
    pages_visited = 1
    skipped = 0

    for link in catalog.problems:
        if link.task_number != task_number:
            skipped += 1
            _report_parse_progress(
                progress,
                records=records,
                skipped=skipped,
                duplicates_skipped=0,
            )
            continue
        if _subcategory_limit_reached(
            subcategory_counts,
            task_number=link.task_number,
            category=link.category,
            subcategory=link.subcategory,
            per_subcategory=per_subcategory,
        ):
            skipped += 1
            _report_parse_progress(
                progress,
                records=records,
                skipped=skipped,
                duplicates_skipped=0,
            )
            continue

        problem_html = _problem_html_for_link(problem_pages, link.source_id)
        if problem_html is None:
            errors.append(
                ProblemValidationError(
                    task_number=link.task_number,
                    source_url=link.source_url,
                    source_id=link.source_id,
                    parse_errors=(MISSING_OFFLINE_SNAPSHOT,),
                    message="offline problem HTML snapshot is missing",
                ),
            )
            _report_parse_progress(
                progress,
                records=records,
                skipped=skipped,
                duplicates_skipped=0,
            )
            continue

        pages_visited += 1
        parsed = parse_problem_html(problem_html, source_url=link.source_url)
        validation = validate_problem(
            parsed,
            task_number=link.task_number,
            category=link.category,
            subcategory=link.subcategory,
        )
        if validation.record is not None:
            records.append(validation.record)
            _increment_subcategory_count(
                subcategory_counts,
                task_number=link.task_number,
                category=link.category,
                subcategory=link.subcategory,
                per_subcategory=per_subcategory,
            )
        if validation.error is not None:
            errors.append(validation.error)
        _report_parse_progress(
            progress,
            records=records,
            skipped=skipped,
            duplicates_skipped=0,
        )

    export = export_task_files(
        task_number=task_number,
        records=records,
        errors=errors,
        output_dir=output_dir,
    )
    _report_parse_progress(
        progress,
        records=records,
        skipped=skipped,
        duplicates_skipped=export.duplicates_skipped,
    )
    report = write_task_report(
        task_number=task_number,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        pages_visited=pages_visited,
        links_found=len(catalog.problems),
        records=tuple(records),
        export=export,
        skipped=skipped,
        output_dir=output_dir,
    )
    debug_result = (
        write_debug_artifacts(
            task_number=task_number,
            catalog_html=catalog_html,
            problem_pages=problem_pages,
            catalog=catalog,
            records=tuple(records),
            errors=tuple(errors),
            output_dir=output_dir,
        )
        if debug
        else None
    )
    if debug_result is not None:
        _report_progress(progress, f"Debug: {debug_result.debug_dir}")
    return OfflinePipelineResult(
        task_number=task_number,
        export=export,
        records=tuple(records),
        errors=tuple(errors),
        catalog_links_found=len(catalog.problems),
        pages_visited=pages_visited,
        skipped=skipped,
        report=report,
        debug=debug_result,
    )


def load_problem_fixture_pages(fixture_dir: Path) -> dict[str, str]:
    """Load bundled problem fixtures keyed by source_id."""
    problem_pages: dict[str, str] = {}
    for fixture_path in sorted(fixture_dir.glob("problem_*.html")):
        html = fixture_path.read_text(encoding="utf-8")
        parsed = parse_problem_html(html)
        if parsed.source_id is not None:
            problem_pages[parsed.source_id] = html
    return problem_pages


def default_fixture_dir() -> Path:
    """Return the bundled offline fixture directory used by test mode."""
    return repository_root() / "backend" / "tests" / "fixtures" / "shkolkovo"


def _discovered_task_numbers(catalog: ParsedCatalog) -> tuple[int, ...]:
    return tuple(
        sorted({problem.task_number for problem in catalog.problems}),
    )


def _problem_html_for_link(
    problem_pages: dict[str, str],
    source_id: str | None,
) -> str | None:
    if source_id is None:
        return None
    return problem_pages.get(source_id)


def _subcategory_limit_reached(
    counts: dict[tuple[int, str | None, str | None], int],
    *,
    task_number: int,
    category: str | None,
    subcategory: str | None,
    per_subcategory: int | None,
) -> bool:
    if per_subcategory is None:
        return False

    key = (task_number, category, subcategory)
    return counts.get(key, 0) >= per_subcategory


def _increment_subcategory_count(
    counts: dict[tuple[int, str | None, str | None], int],
    *,
    task_number: int,
    category: str | None,
    subcategory: str | None,
    per_subcategory: int | None,
) -> None:
    if per_subcategory is None:
        return

    key = (task_number, category, subcategory)
    counts[key] = counts.get(key, 0) + 1


def _report_parse_progress(
    progress: ProgressReporter | None,
    *,
    records: list[ValidatedProblemRecord],
    skipped: int,
    duplicates_skipped: int,
) -> None:
    _report_progress(
        progress,
        "Progress: "
        f"ok={sum(record.parse_status == 'ok' for record in records)}, "
        f"partial={sum(record.parse_status == 'partial' for record in records)}, "
        f"skipped={skipped}, "
        f"image failed={sum(_image_failures(record) for record in records)}, "
        f"duplicates skipped={duplicates_skipped}.",
    )


def _image_failures(record: ValidatedProblemRecord) -> int:
    return sum(
        parse_error.startswith("image_download_failed:")
        for parse_error in record.parse_errors
    )


def _report_progress(
    progress: ProgressReporter | None,
    message: str,
) -> None:
    if progress is not None:
        progress(message)

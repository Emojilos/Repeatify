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
from scripts.shkolkovo_parser.fetcher import (
    CollectionStoppedError,
    FetchError,
    FetchResult,
    ShkolkovoFetcher,
)
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
LIVE_CATALOG_URL = "https://3.shkolkovo.online/catalog?SubjectId=1"
MISSING_OFFLINE_SNAPSHOT = "missing_offline_snapshot"
LIVE_FETCH_FAILED = "live_fetch_failed"
MISSING_SNAPSHOT_DIR = "missing_snapshot_dir"
MISSING_SNAPSHOT_HTML = "missing_snapshot_html"
ProgressReporter = Callable[[str], None]
FetcherFactory = Callable[[], ShkolkovoFetcher]


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


def run_live_smoke_pipeline(
    *,
    task_number: int = DEFAULT_TEST_TASK_NUMBER,
    max_pages: int = 1,
    max_problems: int = 3,
    delay: float = 1.0,
    max_retries: int = 3,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    debug: bool = False,
    fetcher_factory: FetcherFactory | None = None,
) -> OfflinePipelineResult:
    """Run a small live smoke against public pages or write a blocked report."""
    started_at = datetime.now(UTC)
    fetcher = (
        fetcher_factory()
        if fetcher_factory is not None
        else ShkolkovoFetcher(delay=delay, max_retries=max_retries)
    )
    catalog_html = ""
    catalog = ParsedCatalog(problems=(), errors=())
    problem_pages: dict[str, str] = {}
    records: list[ValidatedProblemRecord] = []
    errors: list[ProblemValidationError] = []
    critical_errors: list[dict[str, object]] = []
    pages_visited = 0
    skipped = 0
    status = "completed"

    try:
        _report_progress(
            progress,
            "Live smoke: fetching catalog "
            f"{LIVE_CATALOG_URL} with max_pages={max_pages}.",
        )
        catalog_fetch = fetcher.fetch(
            LIVE_CATALOG_URL,
            snapshot_name=f"live_task_{task_number}_catalog.html",
        )
        pages_visited += 1
        catalog_html = catalog_fetch.html
        catalog = parse_catalog_html(catalog_fetch.html, base_url=catalog_fetch.url)
        _report_progress(
            progress,
            f"Live smoke: found {len(catalog.problems)} catalog links.",
        )

        selected_links = [
            link
            for link in catalog.problems
            if link.task_number == task_number
        ][:max_problems]
        skipped = len(catalog.problems) - len(selected_links)

        for link in selected_links:
            try:
                result = fetcher.fetch(
                    link.source_url,
                    snapshot_name=(
                        f"live_task_{task_number}_problem_"
                        f"{link.source_id or pages_visited + 1}.html"
                    ),
                )
            except CollectionStoppedError as exc:
                status = "blocked"
                error = _validation_error_from_fetch_error(
                    exc,
                    task_number=task_number,
                    source_id=link.source_id,
                )
                errors.append(error)
                critical_errors.append(exc.to_error_record())
                _report_progress(progress, str(exc))
                break
            except FetchError as exc:
                errors.append(
                    _validation_error_from_fetch_error(
                        exc,
                        task_number=task_number,
                        source_id=link.source_id,
                    ),
                )
                _report_progress(progress, str(exc))
                continue

            pages_visited += 1
            _store_problem_page(problem_pages, link.source_id, result)
            parsed = parse_problem_html(result.html, source_url=result.url)
            validation = validate_problem(
                parsed,
                task_number=link.task_number,
                category=link.category,
                subcategory=link.subcategory,
            )
            if validation.record is not None:
                records.append(validation.record)
            if validation.error is not None:
                errors.append(validation.error)
            _report_parse_progress(
                progress,
                records=records,
                skipped=skipped,
                duplicates_skipped=0,
            )
    except CollectionStoppedError as exc:
        pages_visited += 1
        status = "blocked"
        errors.append(
            _validation_error_from_fetch_error(
                exc,
                task_number=task_number,
                source_id=None,
            ),
        )
        critical_errors.append(exc.to_error_record())
        _report_progress(progress, str(exc))
    except FetchError as exc:
        pages_visited += int(exc.attempts > 0)
        status = "blocked"
        errors.append(
            _validation_error_from_fetch_error(
                exc,
                task_number=task_number,
                source_id=None,
            ),
        )
        critical_errors.append(exc.to_error_record())
        _report_progress(progress, str(exc))
    finally:
        fetcher.close()

    export = export_task_files(
        task_number=task_number,
        records=records,
        errors=errors,
        output_dir=output_dir,
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
        status=status,
        critical_errors=tuple(critical_errors),
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


def run_snapshot_pipeline(
    *,
    snapshot_dir: Path,
    task_number: int,
    per_subcategory: int | None = None,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    debug: bool = False,
) -> OfflinePipelineResult:
    """Parse locally saved catalog/problem HTML snapshots for one task."""
    snapshot_dir = snapshot_dir.expanduser()
    if not snapshot_dir.exists() or not snapshot_dir.is_dir():
        return _snapshot_error_result(
            task_number=task_number,
            snapshot_dir=snapshot_dir,
            output_dir=output_dir,
            progress=progress,
            reason=MISSING_SNAPSHOT_DIR,
            message="snapshot directory does not exist",
        )

    catalog_path = _find_snapshot_catalog(snapshot_dir)
    problem_pages = load_problem_snapshot_pages(snapshot_dir)
    if catalog_path is not None:
        _report_progress(
            progress,
            f"Snapshots: using catalog {catalog_path}.",
        )
        return run_offline_pipeline(
            catalog_html=catalog_path.read_text(encoding="utf-8"),
            problem_pages=problem_pages,
            task_number=task_number,
            per_subcategory=per_subcategory,
            output_dir=output_dir,
            progress=progress,
            debug=debug,
        )

    if not problem_pages:
        return _snapshot_error_result(
            task_number=task_number,
            snapshot_dir=snapshot_dir,
            output_dir=output_dir,
            progress=progress,
            reason=MISSING_SNAPSHOT_HTML,
            message="snapshot directory contains no readable problem HTML",
        )

    return run_problem_snapshot_pipeline(
        problem_pages=problem_pages,
        task_number=task_number,
        output_dir=output_dir,
        progress=progress,
        debug=debug,
    )


def run_problem_snapshot_pipeline(
    *,
    problem_pages: dict[str, str],
    task_number: int,
    output_dir: Path | None = None,
    progress: ProgressReporter | None = None,
    debug: bool = False,
) -> OfflinePipelineResult:
    """Parse local problem HTML snapshots when no catalog snapshot exists."""
    started_at = datetime.now(UTC)
    _report_progress(
        progress,
        f"Snapshots: found {len(problem_pages)} problem snapshot(s).",
    )
    records: list[ValidatedProblemRecord] = []
    errors: list[ProblemValidationError] = []

    for snapshot_key, problem_html in problem_pages.items():
        parsed = parse_problem_html(problem_html)
        validation = validate_problem(
            parsed,
            task_number=task_number,
            category=None,
            subcategory=None,
        )
        if validation.record is not None:
            records.append(validation.record)
        if validation.error is not None:
            errors.append(
                _snapshot_validation_error(validation.error, snapshot_key),
            )
        _report_parse_progress(
            progress,
            records=records,
            skipped=0,
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
        skipped=0,
        duplicates_skipped=export.duplicates_skipped,
    )
    report = write_task_report(
        task_number=task_number,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        pages_visited=len(problem_pages),
        links_found=len(problem_pages),
        records=tuple(records),
        export=export,
        skipped=0,
        output_dir=output_dir,
    )
    debug_result = (
        write_debug_artifacts(
            task_number=task_number,
            catalog_html="",
            problem_pages=problem_pages,
            catalog=ParsedCatalog(problems=(), errors=()),
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
        catalog_links_found=len(problem_pages),
        pages_visited=len(problem_pages),
        skipped=0,
        report=report,
        debug=debug_result,
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


def load_problem_snapshot_pages(snapshot_dir: Path) -> dict[str, str]:
    """Load local problem snapshots keyed by source_id or file stem."""
    problem_pages: dict[str, str] = {}
    catalog_path = _find_snapshot_catalog(snapshot_dir)
    for snapshot_path in sorted(snapshot_dir.rglob("*.html")):
        if catalog_path is not None and snapshot_path == catalog_path:
            continue
        if _is_catalog_snapshot_path(snapshot_path):
            continue
        html = snapshot_path.read_text(encoding="utf-8")
        parsed = parse_problem_html(html)
        source_id = parsed.source_id or snapshot_path.stem.removesuffix("_raw")
        problem_pages[source_id] = html
    return problem_pages


def default_fixture_dir() -> Path:
    """Return the bundled offline fixture directory used by test mode."""
    return repository_root() / "backend" / "tests" / "fixtures" / "shkolkovo"


def _snapshot_error_result(
    *,
    task_number: int,
    snapshot_dir: Path,
    output_dir: Path | None,
    progress: ProgressReporter | None,
    reason: str,
    message: str,
) -> OfflinePipelineResult:
    started_at = datetime.now(UTC)
    error = ProblemValidationError(
        task_number=task_number,
        source_url=str(snapshot_dir),
        source_id=None,
        parse_errors=(reason,),
        message=message,
    )
    _report_progress(progress, f"Snapshots: {message}: {snapshot_dir}")
    export = export_task_files(
        task_number=task_number,
        records=(),
        errors=(error,),
        output_dir=output_dir,
    )
    report = write_task_report(
        task_number=task_number,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        pages_visited=0,
        links_found=0,
        records=(),
        export=export,
        skipped=0,
        output_dir=output_dir,
        status="blocked",
        critical_errors=(
            {
                "url": str(snapshot_dir),
                "reason": reason,
                "message": message,
            },
        ),
    )
    return OfflinePipelineResult(
        task_number=task_number,
        export=export,
        records=(),
        errors=(error,),
        catalog_links_found=0,
        pages_visited=0,
        skipped=0,
        report=report,
    )


def _find_snapshot_catalog(snapshot_dir: Path) -> Path | None:
    candidates = (
        "catalog_raw.html",
        "catalog.html",
        "catalog_task.html",
    )
    for candidate in candidates:
        path = snapshot_dir / candidate
        if path.exists() and path.is_file():
            return path

    catalog_paths = sorted(snapshot_dir.glob("catalog*.html"))
    if catalog_paths:
        return catalog_paths[0]
    return None


def _is_catalog_snapshot_path(snapshot_path: Path) -> bool:
    return snapshot_path.name.startswith("catalog") or snapshot_path.name == (
        "catalog_raw.html"
    )


def _snapshot_validation_error(
    error: ProblemValidationError,
    snapshot_key: str,
) -> ProblemValidationError:
    if error.source_url:
        return error
    return ProblemValidationError(
        task_number=error.task_number,
        source_url=snapshot_key,
        source_id=error.source_id,
        parse_errors=error.parse_errors,
        message=error.message,
    )


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


def _store_problem_page(
    problem_pages: dict[str, str],
    source_id: str | None,
    result: FetchResult,
) -> None:
    key = source_id or result.url
    problem_pages[key] = result.html


def _validation_error_from_fetch_error(
    error: FetchError,
    *,
    task_number: int,
    source_id: str | None,
) -> ProblemValidationError:
    reason = getattr(error, "reason", LIVE_FETCH_FAILED)
    return ProblemValidationError(
        task_number=task_number,
        source_url=error.url,
        source_id=source_id,
        parse_errors=(reason,),
        message=str(error),
    )


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

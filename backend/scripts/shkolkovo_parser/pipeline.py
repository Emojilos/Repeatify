"""Offline pipeline assembly for Shkolkovo parser test runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.shkolkovo_parser.catalog_parser import parse_catalog_html
from scripts.shkolkovo_parser.config import repository_root
from scripts.shkolkovo_parser.exporter import ExportResult, export_task_files
from scripts.shkolkovo_parser.problem_parser import parse_problem_html
from scripts.shkolkovo_parser.validator import (
    ProblemValidationError,
    ValidatedProblemRecord,
    validate_problem,
)

DEFAULT_TEST_TASK_NUMBER = 6
MISSING_OFFLINE_SNAPSHOT = "missing_offline_snapshot"


@dataclass(frozen=True)
class OfflinePipelineResult:
    """Files and counters produced by one offline task pipeline run."""

    task_number: int
    export: ExportResult
    records: tuple[ValidatedProblemRecord, ...]
    errors: tuple[ProblemValidationError, ...]
    catalog_links_found: int

    @property
    def duplicates_skipped(self) -> int:
        """Number of dataset records skipped because they already existed."""
        return self.export.duplicates_skipped


def run_fixture_pipeline(
    *,
    task_number: int = DEFAULT_TEST_TASK_NUMBER,
    per_subcategory: int | None = None,
    fixture_dir: Path | None = None,
    output_dir: Path | None = None,
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
    )


def run_offline_pipeline(
    *,
    catalog_html: str,
    problem_pages: dict[str, str],
    task_number: int,
    per_subcategory: int | None = None,
    output_dir: Path | None = None,
) -> OfflinePipelineResult:
    """Parse saved catalog/problem HTML and export one task dataset."""
    catalog = parse_catalog_html(catalog_html)
    records: list[ValidatedProblemRecord] = []
    errors: list[ProblemValidationError] = []
    subcategory_counts: dict[tuple[int, str | None, str | None], int] = {}

    for link in catalog.problems:
        if link.task_number != task_number:
            continue
        if _subcategory_limit_reached(
            subcategory_counts,
            task_number=link.task_number,
            category=link.category,
            subcategory=link.subcategory,
            per_subcategory=per_subcategory,
        ):
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
            continue

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

    export = export_task_files(
        task_number=task_number,
        records=records,
        errors=errors,
        output_dir=output_dir,
    )
    return OfflinePipelineResult(
        task_number=task_number,
        export=export,
        records=tuple(records),
        errors=tuple(errors),
        catalog_links_found=len(catalog.problems),
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

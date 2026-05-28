"""CLI contract for the Shkolkovo parser."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass

from scripts.shkolkovo_parser import __version__
from scripts.shkolkovo_parser.pipeline import (
    DEFAULT_TEST_TASK_NUMBER,
    OfflineAllPipelineResult,
    OfflinePipelineResult,
    run_all_fixture_pipeline,
    run_fixture_pipeline,
)

MIN_TASK_NUMBER = 1
MAX_TASK_NUMBER = 19


@dataclass(frozen=True)
class ParserOptions:
    """Validated parser options parsed from the command line."""

    mode: str
    task_number: int | None
    per_subcategory: int | None
    max_pages: int | None
    max_problems: int | None
    delay: float
    max_retries: int
    image_workers: int
    debug: bool


def task_number(value: str) -> int:
    """Parse a task number in the supported EGE task range."""
    number = _int(value)
    if not MIN_TASK_NUMBER <= number <= MAX_TASK_NUMBER:
        msg = (
            f"task number must be between {MIN_TASK_NUMBER} and "
            f"{MAX_TASK_NUMBER}"
        )
        raise argparse.ArgumentTypeError(msg)
    return number


def positive_int(value: str) -> int:
    """Parse a positive integer for CLI limits."""
    number = _positive_int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def non_negative_int(value: str) -> int:
    """Parse a non-negative integer."""
    number = _int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must be at least 0")
    return number


def non_negative_float(value: str) -> float:
    """Parse a non-negative float."""
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be a number") from exc
    if number < 0:
        raise argparse.ArgumentTypeError("value must be at least 0")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Build the MVP CLI surface for the parser package."""
    parser = argparse.ArgumentParser(
        prog="python -m scripts.shkolkovo_parser",
        description="Collect public Shkolkovo problem data.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--mode",
        choices=("test", "all"),
        default="test",
        help="run mode: test smoke collection or all public catalog pages",
    )
    parser.add_argument(
        "--task-number",
        type=task_number,
        help="limit collection to one EGE task number from 1 to 19",
    )
    parser.add_argument(
        "--per-subcategory",
        "--per-prototype",
        dest="per_subcategory",
        metavar="N",
        type=positive_int,
        help="limit collected problems per subcategory/prototype",
    )
    parser.add_argument(
        "--max-pages",
        type=positive_int,
        help="limit catalog pages for smoke/debug runs",
    )
    parser.add_argument(
        "--max-problems",
        type=positive_int,
        help="limit problem pages for smoke/debug runs",
    )
    parser.add_argument(
        "--delay",
        default=1.0,
        type=non_negative_float,
        help="delay in seconds between HTML requests",
    )
    parser.add_argument(
        "--max-retries",
        default=3,
        type=non_negative_int,
        help="number of retries for temporary request failures",
    )
    parser.add_argument(
        "--image-workers",
        default=2,
        type=positive_int,
        help="maximum parallel image downloads",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="write extended local debug artifacts",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> ParserOptions:
    """Parse and validate parser CLI arguments."""
    namespace = build_parser().parse_args(argv)
    return ParserOptions(
        mode=namespace.mode,
        task_number=namespace.task_number,
        per_subcategory=namespace.per_subcategory,
        max_pages=namespace.max_pages,
        max_problems=namespace.max_problems,
        delay=namespace.delay,
        max_retries=namespace.max_retries,
        image_workers=namespace.image_workers,
        debug=namespace.debug,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the parser CLI."""
    options = parse_args(argv)
    if options.mode == "test":
        result = run_fixture_pipeline(
            task_number=options.task_number or DEFAULT_TEST_TASK_NUMBER,
            per_subcategory=options.per_subcategory,
            progress=print,
        )
        print(
            "Offline test pipeline completed: "
            f"{result.export.records_written} records, "
            f"{result.export.errors_written} errors, "
            f"{result.duplicates_skipped} duplicates skipped.",
        )
        print(f"Output: {result.export.output_file}")
        print(f"Errors: {result.export.errors_file}")
        print(f"Report: {result.report.report_file}")
        return 0

    result = run_all_fixture_pipeline(
        per_subcategory=options.per_subcategory,
        progress=print,
        parameters=_run_parameters(options),
    )
    _print_all_result(result)
    return 0


def _print_all_result(result: OfflineAllPipelineResult) -> None:
    totals = result.run_report.report["totals"]
    print(
        "All-mode offline pipeline completed: "
        f"{totals['tasks_processed']} tasks, "
        f"{totals['parsed_ok']} ok, "
        f"{totals['parsed_partial']} partial, "
        f"{totals['duplicates_skipped']} duplicates skipped.",
    )
    for task_result in result.task_results:
        _print_task_result(task_result)
    print(f"Run report: {result.run_report.report_file}")


def _print_task_result(result: OfflinePipelineResult) -> None:
    print(
        f"Task {result.task_number}: "
        f"output={result.export.output_file}, "
        f"errors={result.export.errors_file}, "
        f"report={result.report.report_file}",
    )


def _run_parameters(options: ParserOptions) -> dict[str, object]:
    return {
        "mode": options.mode,
        "task_number": options.task_number,
        "per_subcategory": options.per_subcategory,
        "max_pages": options.max_pages,
        "max_problems": options.max_problems,
        "delay": options.delay,
        "max_retries": options.max_retries,
        "image_workers": options.image_workers,
        "debug": options.debug,
    }


def _positive_int(value: str) -> int:
    number = _int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")
    return number


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc

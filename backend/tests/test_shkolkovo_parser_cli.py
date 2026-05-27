"""Tests for the Shkolkovo parser CLI contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.shkolkovo_parser.cli import parse_args


def test_mvp_help_lists_supported_options() -> None:
    result = run_parser_cli("--help")

    assert result.returncode == 0
    assert "--mode" in result.stdout
    assert "{test,all}" in result.stdout
    assert "--task-number" in result.stdout
    assert "--per-subcategory" in result.stdout
    assert "--per-prototype" in result.stdout
    assert "--max-pages" in result.stdout
    assert "--max-problems" in result.stdout
    assert "--delay" in result.stdout
    assert "--max-retries" in result.stdout
    assert "--image-workers" in result.stdout
    assert "--debug" in result.stdout


def test_cli_accepts_mvp_options_and_alias() -> None:
    options = parse_args(
        [
            "--mode",
            "all",
            "--task-number",
            "6",
            "--per-prototype",
            "3",
            "--max-pages",
            "2",
            "--max-problems",
            "5",
            "--delay",
            "0.25",
            "--max-retries",
            "4",
            "--image-workers",
            "2",
            "--debug",
        ],
    )

    assert options.mode == "all"
    assert options.task_number == 6
    assert options.per_subcategory == 3
    assert options.max_pages == 2
    assert options.max_problems == 5
    assert options.delay == 0.25
    assert options.max_retries == 4
    assert options.image_workers == 2
    assert options.debug is True


@pytest.mark.parametrize("task_number", ["0", "20"])
def test_cli_rejects_task_number_outside_supported_range(
    task_number: str,
) -> None:
    result = run_parser_cli("--task-number", task_number)

    assert result.returncode != 0
    assert "task number must be between 1 and 19" in result.stderr


@pytest.mark.parametrize(
    ("option", "value", "message"),
    [
        ("--max-pages", "0", "value must be at least 1"),
        ("--max-problems", "-1", "value must be at least 1"),
        ("--delay", "-0.1", "value must be at least 0"),
        ("--max-retries", "-1", "value must be at least 0"),
        ("--image-workers", "0", "value must be at least 1"),
    ],
)
def test_cli_rejects_invalid_numeric_values(
    option: str,
    value: str,
    message: str,
) -> None:
    result = run_parser_cli(option, value)

    assert result.returncode != 0
    assert message in result.stderr


def run_parser_cli(*args: str) -> subprocess.CompletedProcess[str]:
    backend_dir = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, "-m", "scripts.shkolkovo_parser", *args],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        text=True,
    )

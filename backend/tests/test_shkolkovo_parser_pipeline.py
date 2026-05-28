"""Tests for the Shkolkovo parser offline pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.shkolkovo_parser.pipeline import (
    MISSING_OFFLINE_SNAPSHOT,
    run_fixture_pipeline,
    run_offline_pipeline,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def test_fixture_pipeline_exports_task_6_json_files(tmp_path: Path) -> None:
    result = run_fixture_pipeline(output_dir=tmp_path)

    assert result.task_number == 6
    assert result.catalog_links_found == 4
    assert result.export.output_file == tmp_path / "task_6.json"
    assert result.export.errors_file == tmp_path / "task_6_errors.json"
    assert result.export.records_written == 3
    assert result.export.errors_written == 0
    assert sorted(path.name for path in tmp_path.glob("task_*.json")) == [
        "task_6.json",
        "task_6_errors.json",
    ]

    records = json.loads(result.export.output_file.read_text(encoding="utf-8"))
    errors = json.loads(result.export.errors_file.read_text(encoding="utf-8"))

    assert errors == []
    assert [record["source_id"] for record in records] == [
        "100601",
        "100602",
        "100603",
    ]
    assert {record["task_number"] for record in records} == {6}
    assert records[0]["parse_status"] == "ok"
    assert records[1]["parse_status"] == "partial"
    assert records[1]["parse_errors"] == ["missing_correct_answer"]
    assert records[2]["problem_text"].count("$") >= 4


def test_offline_pipeline_records_missing_problem_snapshot(
    tmp_path: Path,
) -> None:
    catalog_html = (FIXTURE_DIR / "catalog_task_6.html").read_text(
        encoding="utf-8",
    )

    result = run_offline_pipeline(
        catalog_html=catalog_html,
        problem_pages={},
        task_number=6,
        output_dir=tmp_path,
    )

    assert result.export.records_written == 0
    assert result.export.errors_written == 3

    errors = json.loads(result.export.errors_file.read_text(encoding="utf-8"))
    assert {error["error"] for error in errors} == {MISSING_OFFLINE_SNAPSHOT}


def test_fixture_pipeline_limits_records_per_subcategory(
    tmp_path: Path,
) -> None:
    result = run_fixture_pipeline(
        per_subcategory=1,
        output_dir=tmp_path,
    )

    assert result.export.records_written == 2
    assert result.export.errors_written == 0

    records = json.loads(result.export.output_file.read_text(encoding="utf-8"))
    subcategories = [record["subcategory"] for record in records]

    assert [record["source_id"] for record in records] == ["100601", "100603"]
    assert subcategories == ["Треугольники", "Окружности"]
    assert len(subcategories) == len(set(subcategories))


def test_cli_test_mode_runs_offline_fixture_pipeline() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.shkolkovo_parser",
            "--mode",
            "test",
        ],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Offline test pipeline completed" in result.stdout
    assert "task_6.json" in result.stdout
    assert "task_6_errors.json" in result.stdout


def test_cli_passes_per_subcategory_limit_to_fixture_pipeline() -> None:
    result = run_parser_cli(
        "--mode",
        "test",
        "--task-number",
        "6",
        "--per-subcategory",
        "1",
    )

    assert result.returncode == 0
    assert "Offline test pipeline completed: 2 records, 0 errors." in result.stdout


def test_cli_per_prototype_alias_limits_fixture_pipeline() -> None:
    result = run_parser_cli(
        "--mode",
        "test",
        "--task-number",
        "6",
        "--per-prototype",
        "1",
    )

    assert result.returncode == 0
    assert "Offline test pipeline completed: 2 records, 0 errors." in result.stdout


def run_parser_cli(*args: str) -> subprocess.CompletedProcess[str]:
    backend_dir = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, "-m", "scripts.shkolkovo_parser", *args],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        text=True,
    )

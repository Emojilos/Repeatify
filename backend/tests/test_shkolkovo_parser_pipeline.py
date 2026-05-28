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
    assert result.duplicates_skipped == 0
    assert result.pages_visited == 4
    assert result.skipped == 1
    assert result.report.report_file == tmp_path / "task_6_report.json"
    assert sorted(path.name for path in tmp_path.glob("task_*.json")) == [
        "task_6.json",
        "task_6_errors.json",
        "task_6_report.json",
    ]

    records = json.loads(result.export.output_file.read_text(encoding="utf-8"))
    errors = json.loads(result.export.errors_file.read_text(encoding="utf-8"))
    report = json.loads(result.report.report_file.read_text(encoding="utf-8"))

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
    assert report["task_number"] == 6
    assert report["pages_visited"] == 4
    assert report["links_found"] == 4
    assert report["parsed_ok"] == 2
    assert report["parsed_partial"] == 1
    assert report["duplicates_skipped"] == 0
    assert report["skipped"] == 1
    assert report["images_downloaded"] == 0
    assert report["images_failed"] == 0
    assert report["output_file"].endswith("task_6.json")
    assert report["errors_file"].endswith("task_6_errors.json")
    assert report["started_at"].endswith("Z")
    assert report["finished_at"].endswith("Z")


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
    assert result.pages_visited == 1
    assert result.skipped == 1

    errors = json.loads(result.export.errors_file.read_text(encoding="utf-8"))
    assert {error["error"] for error in errors} == {MISSING_OFFLINE_SNAPSHOT}


def test_fixture_pipeline_repeat_run_skips_existing_records(
    tmp_path: Path,
) -> None:
    first_result = run_fixture_pipeline(output_dir=tmp_path)
    second_result = run_fixture_pipeline(output_dir=tmp_path)

    assert first_result.export.records_written == 3
    assert first_result.duplicates_skipped == 0
    assert second_result.export.records_written == 3
    assert second_result.duplicates_skipped == 3

    records = json.loads(second_result.export.output_file.read_text(encoding="utf-8"))
    report = json.loads(second_result.report.report_file.read_text(encoding="utf-8"))
    assert [record["source_id"] for record in records] == [
        "100601",
        "100602",
        "100603",
    ]
    assert report["duplicates_skipped"] == 3


def test_fixture_pipeline_limits_records_per_subcategory(
    tmp_path: Path,
) -> None:
    result = run_fixture_pipeline(
        per_subcategory=1,
        output_dir=tmp_path,
    )

    assert result.export.records_written == 2
    assert result.export.errors_written == 0
    assert result.skipped == 2

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
    assert "Task 6: found 4 catalog links." in result.stdout
    assert "Progress: ok=" in result.stdout
    assert "partial=" in result.stdout
    assert "skipped=" in result.stdout
    assert "image failed=" in result.stdout
    assert "duplicates skipped=" in result.stdout
    assert "Offline test pipeline completed" in result.stdout
    assert "task_6.json" in result.stdout
    assert "task_6_errors.json" in result.stdout
    assert "task_6_report.json" in result.stdout


def test_fixture_pipeline_reports_console_progress(tmp_path: Path) -> None:
    messages: list[str] = []

    run_fixture_pipeline(output_dir=tmp_path, progress=messages.append)

    assert messages[0] == "Task 6: found 4 catalog links."
    assert messages[-1] == (
        "Progress: ok=2, partial=1, skipped=1, "
        "image failed=0, duplicates skipped=0."
    )


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
    assert "Offline test pipeline completed:" in result.stdout
    assert "duplicates skipped." in result.stdout


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
    assert "Offline test pipeline completed:" in result.stdout
    assert "duplicates skipped." in result.stdout


def run_parser_cli(*args: str) -> subprocess.CompletedProcess[str]:
    backend_dir = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [sys.executable, "-m", "scripts.shkolkovo_parser", *args],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        text=True,
    )

"""Tests for the Shkolkovo parser offline pipeline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.shkolkovo_parser.pipeline import (
    MISSING_OFFLINE_SNAPSHOT,
    run_all_fixture_pipeline,
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


def test_fixture_pipeline_writes_debug_artifacts_without_dataset_debug_fields(
    tmp_path: Path,
) -> None:
    result = run_fixture_pipeline(output_dir=tmp_path, debug=True)

    assert result.debug is not None
    assert result.debug.debug_dir == tmp_path / "debug" / "task_6"
    assert (result.debug.debug_dir / "catalog_raw.html").exists()
    assert (result.debug.debug_dir / "catalog_parsed.json").exists()
    assert (result.debug.debug_dir / "validated_records.json").exists()
    assert (result.debug.debug_dir / "validation_errors.json").exists()
    assert (
        result.debug.debug_dir / "problem_pages" / "100601_raw.html"
    ).exists()

    debug_catalog = json.loads(
        (result.debug.debug_dir / "catalog_parsed.json").read_text(
            encoding="utf-8",
        ),
    )
    records = json.loads(result.export.output_file.read_text(encoding="utf-8"))

    assert debug_catalog["problems"][0]["source_id"] == "100601"
    assert "raw" not in records[0]
    assert "debug" not in records[0]
    assert all("html" not in key for record in records for key in record)


def test_all_fixture_pipeline_exports_each_discovered_task_and_run_report(
    tmp_path: Path,
) -> None:
    result = run_all_fixture_pipeline(
        output_dir=tmp_path,
        parameters={"mode": "all", "per_subcategory": None},
    )

    assert result.task_numbers == (6, 7)
    assert [task_result.task_number for task_result in result.task_results] == [6, 7]
    assert sorted(path.name for path in tmp_path.glob("task_*.json")) == [
        "task_6.json",
        "task_6_errors.json",
        "task_6_report.json",
        "task_7.json",
        "task_7_errors.json",
        "task_7_report.json",
    ]
    assert result.run_report.report_file.name.startswith("run_report_")
    assert result.run_report.report_file.name.endswith(".json")

    run_report = json.loads(
        result.run_report.report_file.read_text(encoding="utf-8"),
    )
    task_reports = [
        json.loads(
            task_result.report.report_file.read_text(encoding="utf-8"),
        )
        for task_result in result.task_results
    ]

    assert run_report["mode"] == "all"
    assert run_report["parameters"] == {"mode": "all", "per_subcategory": None}
    assert run_report["critical_errors"] == []
    assert run_report["totals"] == {
        "tasks_processed": 2,
        "pages_visited": sum(report["pages_visited"] for report in task_reports),
        "links_found": sum(report["links_found"] for report in task_reports),
        "parsed_ok": sum(report["parsed_ok"] for report in task_reports),
        "parsed_partial": sum(
            report["parsed_partial"] for report in task_reports
        ),
        "duplicates_skipped": sum(
            report["duplicates_skipped"] for report in task_reports
        ),
        "skipped": sum(report["skipped"] for report in task_reports),
        "images_downloaded": sum(
            report["images_downloaded"] for report in task_reports
        ),
        "images_failed": sum(report["images_failed"] for report in task_reports),
    }
    assert [task["task_number"] for task in run_report["tasks"]] == [6, 7]
    assert run_report["tasks"][0]["report_file"].endswith("task_6_report.json")
    assert run_report["tasks"][1]["report_file"].endswith("task_7_report.json")
    assert run_report["started_at"].endswith("Z")
    assert run_report["finished_at"].endswith("Z")


def test_cli_all_mode_runs_all_discovered_fixture_tasks() -> None:
    result = run_parser_cli("--mode", "all")

    assert result.returncode == 0
    assert "All mode: discovered task numbers 6, 7." in result.stdout
    assert "All-mode offline pipeline completed:" in result.stdout
    assert "Task 6: output=" in result.stdout
    assert "Task 7: output=" in result.stdout
    assert "Run report:" in result.stdout
    assert "run_report_" in result.stdout


def test_cli_debug_mode_writes_default_debug_artifacts() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    debug_dir = backend_dir.parent / "data" / "raw" / "shkolkovo" / "debug"

    result = run_parser_cli("--mode", "test", "--debug")

    assert result.returncode == 0
    assert "Debug:" in result.stdout
    assert (debug_dir / "task_6" / "catalog_raw.html").exists()


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

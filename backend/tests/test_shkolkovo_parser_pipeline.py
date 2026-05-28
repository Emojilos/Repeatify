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
    assert result.catalog_links_found == 3
    assert result.export.output_file == tmp_path / "task_6.json"
    assert result.export.errors_file == tmp_path / "task_6_errors.json"
    assert result.export.records_written == 3
    assert result.export.errors_written == 0

    records = json.loads(result.export.output_file.read_text(encoding="utf-8"))
    errors = json.loads(result.export.errors_file.read_text(encoding="utf-8"))

    assert errors == []
    assert [record["source_id"] for record in records] == [
        "100601",
        "100602",
        "100603",
    ]
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

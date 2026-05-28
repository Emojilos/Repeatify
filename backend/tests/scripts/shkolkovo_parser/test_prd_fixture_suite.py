"""Fixture-based PRD coverage for the Shkolkovo parser pipeline."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import httpx

from scripts.shkolkovo_parser.catalog_parser import parse_catalog_html
from scripts.shkolkovo_parser.exporter import (
    build_dataset_record,
    export_task_files,
)
from scripts.shkolkovo_parser.image_downloader import (
    download_problem_images,
    image_download_failed_error,
)
from scripts.shkolkovo_parser.normalizer import normalize_problem_html
from scripts.shkolkovo_parser.pipeline import run_fixture_pipeline
from scripts.shkolkovo_parser.problem_parser import ParsedProblem, parse_problem_html
from scripts.shkolkovo_parser.validator import (
    MISSING_CORRECT_ANSWER,
    MISSING_PROBLEM_TEXT,
    ParseStatus,
    ValidatedProblemRecord,
    validate_problem,
)

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "shkolkovo"


def test_catalog_and_basic_problem_fixture_cover_classification_and_answer() -> None:
    catalog = parse_catalog_html(_fixture("catalog_task_6.html"))

    link = catalog.problems[0]
    problem = parse_problem_html(
        _fixture("problem_basic.html"),
        source_url=link.source_url,
    )
    validation = validate_problem(
        problem,
        task_number=link.task_number,
        category=link.category,
        subcategory=link.subcategory,
    )

    assert catalog.errors[0].reason == "task_number_out_of_range"
    assert link.task_number == 6
    assert link.category == "Планиметрия"
    assert link.subcategory == "Треугольники"
    assert validation.record is not None
    assert validation.record.parse_status == "ok"
    assert validation.record.correct_answer == "10"
    assert validation.record.source_id == "100601"


def test_missing_answer_fixture_is_partial_but_stays_usable() -> None:
    problem = parse_problem_html(_fixture("problem_missing_answer.html"))

    validation = validate_problem(
        problem,
        task_number=6,
        category="Планиметрия",
        subcategory="Треугольники",
    )

    assert validation.error is None
    assert validation.record is not None
    assert validation.record.parse_status == "partial"
    assert validation.record.correct_answer is None
    assert validation.record.parse_errors == (MISSING_CORRECT_ANSWER,)


def test_latex_fixture_normalizes_math_and_removes_service_dom() -> None:
    text = normalize_problem_html(_fixture("problem_with_latex.html"))

    assert text == (
        "Найдите радиус окружности, если ее длина равна $18\\pi$. "
        "$$C = 2\\pi r$$"
    )
    assert "Показать ответ" not in text
    assert "MathJax rendered content" not in text


def test_image_fixture_extracts_condition_images_without_solution_images() -> None:
    problem = parse_problem_html(
        _fixture("problem_with_images.html"),
        source_url="https://3.shkolkovo.online/problem/100604?SubjectId=1",
    )
    validation = validate_problem(problem, task_number=6)

    assert validation.record is not None
    assert validation.record.source_image_urls == (
        "https://3.shkolkovo.online/media/problems/100604/triangle.png",
        "https://static.shkolkovo.online/problems/100604/angle.png",
    )
    assert all("solution" not in url for url in validation.record.source_image_urls)
    assert build_dataset_record(validation.record)["solution_images"] == []


def test_missing_problem_text_goes_to_errors_file_record(tmp_path: Path) -> None:
    problem = ParsedProblem(
        problem_text="",
        correct_answer="42",
        source_url="https://3.shkolkovo.online/problem/100699?SubjectId=1",
        source_id="100699",
    )
    validation = validate_problem(problem, task_number=6)

    assert validation.record is None
    assert validation.error is not None
    assert validation.error.parse_errors == (MISSING_PROBLEM_TEXT,)

    export = export_task_files(
        task_number=6,
        records=(),
        errors=(validation.error,),
        output_dir=tmp_path,
    )

    records = json.loads(export.output_file.read_text(encoding="utf-8"))
    errors = json.loads(export.errors_file.read_text(encoding="utf-8"))
    assert records == []
    assert errors[0]["error"] == MISSING_PROBLEM_TEXT
    assert errors[0]["source_id"] == "100699"


def test_export_schema_and_deduplication_are_stable(tmp_path: Path) -> None:
    record = _validated_record()

    first = export_task_files(task_number=6, records=(record,), output_dir=tmp_path)
    second = export_task_files(
        task_number=6,
        records=(
            replace(
                record,
                correct_answer="new answer should not overwrite duplicate",
            ),
        ),
        output_dir=tmp_path,
    )

    records = json.loads(second.output_file.read_text(encoding="utf-8"))
    assert first.records_written == 1
    assert second.records_written == 1
    assert second.duplicates_skipped == 1
    assert records[0]["correct_answer"] == "10"
    assert records[0]["difficulty"] == "medium"
    assert records[0]["answer_tolerance"] == 0
    assert records[0]["solution_markdown"] is None
    assert records[0]["hints"] == []
    assert records[0]["content_hash"]


def test_reporting_covers_fixture_pipeline_counters(tmp_path: Path) -> None:
    result = run_fixture_pipeline(output_dir=tmp_path)

    report = json.loads(result.report.report_file.read_text(encoding="utf-8"))
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


def test_image_download_failures_remain_partial_records(tmp_path: Path) -> None:
    ok_url = "https://3.shkolkovo.online/media/problems/100601/triangle.png"
    failed_url = "https://3.shkolkovo.online/media/problems/100601/missing.png"

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == ok_url:
            return httpx.Response(200, content=b"png", request=request)
        return httpx.Response(404, request=request)

    downloaded = download_problem_images(
        _validated_record(source_image_urls=(ok_url, failed_url)),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        data_dir=tmp_path / "data" / "raw" / "shkolkovo",
        repository_root_path=tmp_path,
    )

    assert len(downloaded.downloads) == 1
    assert len(downloaded.failures) == 1
    assert downloaded.record.parse_status == "partial"
    assert downloaded.record.parse_errors == (
        image_download_failed_error(failed_url),
    )
    assert downloaded.record.source_image_urls == (ok_url, failed_url)


def _fixture(filename: str) -> str:
    return (FIXTURE_DIR / filename).read_text(encoding="utf-8")


def _validated_record(
    *,
    source_image_urls: tuple[str, ...] = (),
) -> ValidatedProblemRecord:
    return ValidatedProblemRecord(
        task_number=6,
        problem_text="В треугольнике ABC найдите AB.",
        correct_answer="10",
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
        source_id="100601",
        category="Планиметрия",
        subcategory="Треугольники",
        parse_status=cast(ParseStatus, "ok"),
        parse_errors=(),
        source_image_urls=source_image_urls,
    )

"""Tests for Shkolkovo parser content_hash identity."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast

from scripts.shkolkovo_parser.exporter import (
    build_dataset_record,
    content_hash_for_problem,
)
from scripts.shkolkovo_parser.normalizer import normalize_problem_html
from scripts.shkolkovo_parser.validator import ParseStatus, ValidatedProblemRecord

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def _validated_record(
    *,
    task_number: int = 6,
    problem_text: str = "Найдите радиус окружности. $C = 2\\pi r$",
    correct_answer: str | None = "9",
    source_url: str = "https://3.shkolkovo.online/problem/100603?SubjectId=1",
    source_id: str | None = "100603",
    category: str | None = "Планиметрия",
    subcategory: str | None = "Окружности",
    parse_status: str = "ok",
    parse_errors: tuple[str, ...] = (),
    source_image_urls: tuple[str, ...] = (),
    problem_images: tuple[str, ...] = (),
) -> ValidatedProblemRecord:
    return ValidatedProblemRecord(
        task_number=task_number,
        problem_text=problem_text,
        correct_answer=correct_answer,
        source_url=source_url,
        source_id=source_id,
        category=category,
        subcategory=subcategory,
        parse_status=cast(ParseStatus, parse_status),
        parse_errors=parse_errors,
        source_image_urls=source_image_urls,
        problem_images=problem_images,
    )


def test_content_hash_uses_task_number_and_normalized_problem_text() -> None:
    html = (FIXTURE_DIR / "problem_with_latex.html").read_text(encoding="utf-8")
    normalized_text = normalize_problem_html(html)

    content_hash = content_hash_for_problem(
        task_number=6,
        problem_text=normalized_text,
    )

    expected_payload = f"6\n{normalized_text}".encode("utf-8")
    assert content_hash == hashlib.sha256(expected_payload).hexdigest()


def test_content_hash_ignores_answer_source_images_and_parse_status() -> None:
    problem_text = "Найдите радиус окружности. $C = 2\\pi r$"
    first_record = build_dataset_record(
        _validated_record(problem_text=problem_text),
    )
    second_record = build_dataset_record(
        _validated_record(
            problem_text=problem_text,
            correct_answer=None,
            source_url="https://mirror.example/problem/changed",
            source_id="different-source-id",
            category="Алгебра",
            subcategory="Уравнения",
            parse_status="partial",
            parse_errors=("missing_correct_answer",),
            source_image_urls=("https://example.test/image.png",),
            problem_images=("data/raw/shkolkovo/images/task_6/local.png",),
        ),
    )

    assert first_record["content_hash"] == second_record["content_hash"]


def test_content_hash_changes_when_task_number_or_problem_text_changes() -> None:
    content_hash = content_hash_for_problem(
        task_number=6,
        problem_text="Найдите радиус окружности.",
    )

    assert content_hash != content_hash_for_problem(
        task_number=7,
        problem_text="Найдите радиус окружности.",
    )
    assert content_hash != content_hash_for_problem(
        task_number=6,
        problem_text="Найдите диаметр окружности.",
    )

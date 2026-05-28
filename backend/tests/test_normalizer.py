"""Tests for Shkolkovo problem text normalization."""

from __future__ import annotations

from pathlib import Path

from scripts.shkolkovo_parser.normalizer import (
    normalize_problem_html,
    normalize_problem_text,
)
from scripts.shkolkovo_parser.problem_parser import ParsedProblem, parse_problem_html

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def test_normalizer_preserves_readable_markdown_latex_from_fixture() -> None:
    html = (FIXTURE_DIR / "problem_with_latex.html").read_text(encoding="utf-8")

    text = normalize_problem_html(html)

    assert text == (
        "Найдите радиус окружности, если ее длина равна $18\\pi$. "
        "$$C = 2\\pi r$$"
    )


def test_normalizer_removes_service_dom_text() -> None:
    html = (FIXTURE_DIR / "problem_with_latex.html").read_text(encoding="utf-8")

    text = normalize_problem_html(html)

    assert "Показать ответ" not in text
    assert "меню" not in text.lower()
    assert "MathJax DOM-разметка" not in text
    assert "MathJax rendered content" not in text
    assert "mjx-container" not in text


def test_normalizer_is_idempotent_for_normalized_text() -> None:
    text = "Найдите радиус окружности, если C = $2\\pi r$. $$r = 9$$"

    assert normalize_problem_text(normalize_problem_text(text)) == text


def test_problem_parser_returns_normalized_latex_problem_text() -> None:
    html = (FIXTURE_DIR / "problem_with_latex.html").read_text(encoding="utf-8")

    problem = parse_problem_html(html)

    assert problem == ParsedProblem(
        problem_text=(
            "Найдите радиус окружности, если ее длина равна $18\\pi$. "
            "$$C = 2\\pi r$$"
        ),
        correct_answer="9",
        source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
        source_id="100603",
    )

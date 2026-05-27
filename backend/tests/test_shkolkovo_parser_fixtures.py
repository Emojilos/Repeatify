"""Tests for Shkolkovo parser HTML fixtures."""

from __future__ import annotations

from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def test_shkolkovo_fixture_files_exist() -> None:
    expected_files = {
        "catalog_task_6.html",
        "problem_basic.html",
        "problem_missing_answer.html",
        "problem_with_latex.html",
    }

    assert {path.name for path in FIXTURE_DIR.glob("*.html")} == expected_files


def test_catalog_fixture_contains_task_links_and_classification() -> None:
    html = (FIXTURE_DIR / "catalog_task_6.html").read_text(encoding="utf-8")

    assert 'data-fixture="shkolkovo-catalog"' in html
    assert 'data-task-number="6"' in html
    assert 'data-category="Планиметрия"' in html
    assert 'data-subcategory="Треугольники"' in html
    assert 'data-subcategory="Окружности"' in html
    assert 'class="problem-link"' in html
    assert "https://3.shkolkovo.online/problem/100601?SubjectId=1" in html


def test_problem_fixtures_cover_basic_missing_answer_and_latex_cases() -> None:
    basic = (FIXTURE_DIR / "problem_basic.html").read_text(encoding="utf-8")
    missing_answer = (FIXTURE_DIR / "problem_missing_answer.html").read_text(
        encoding="utf-8",
    )
    latex = (FIXTURE_DIR / "problem_with_latex.html").read_text(encoding="utf-8")

    assert 'data-source-id="100601"' in basic
    assert 'class="problem-text"' in basic
    assert 'class="correct-answer">10<' in basic

    assert 'data-source-id="100602"' in missing_answer
    assert 'class="problem-text"' in missing_answer
    assert "correct-answer" not in missing_answer

    assert 'data-source-id="100603"' in latex
    assert 'data-tex="18\\pi"' in latex
    assert 'data-tex="C = 2\\pi r"' in latex
    assert "MathJax DOM-разметка" in latex

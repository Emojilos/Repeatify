"""Tests for parsing Shkolkovo problem pages."""

from __future__ import annotations

from pathlib import Path

from scripts.shkolkovo_parser.problem_parser import (
    ParsedProblem,
    parse_problem_html,
    source_id_from_url,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def test_problem_parser_extracts_basic_problem_answer_and_source_metadata() -> None:
    html = (FIXTURE_DIR / "problem_basic.html").read_text(encoding="utf-8")

    problem = parse_problem_html(
        html,
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
    )

    assert problem == ParsedProblem(
        problem_text=(
            "В треугольнике ABC угол C равен 90 градусов, AC = 6, BC = 8. "
            "Найдите AB."
        ),
        correct_answer="10",
        source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
        source_id="100601",
    )


def test_problem_parser_uses_fixture_source_url_when_not_passed() -> None:
    html = (FIXTURE_DIR / "problem_basic.html").read_text(encoding="utf-8")

    problem = parse_problem_html(html)

    assert problem.source_url == "https://3.shkolkovo.online/problem/100601?SubjectId=1"
    assert problem.source_id == "100601"


def test_problem_parser_allows_missing_public_answer() -> None:
    html = (FIXTURE_DIR / "problem_missing_answer.html").read_text(
        encoding="utf-8",
    )

    problem = parse_problem_html(
        html,
        source_url="https://3.shkolkovo.online/problem/100602?SubjectId=1",
    )

    assert problem.problem_text == (
        "Катеты прямоугольного треугольника равны 5 и 12. Найдите гипотенузу."
    )
    assert problem.correct_answer is None
    assert problem.source_url == "https://3.shkolkovo.online/problem/100602?SubjectId=1"
    assert problem.source_id == "100602"


def test_problem_parser_extracts_problem_image_source_urls_only() -> None:
    html = (FIXTURE_DIR / "problem_with_images.html").read_text(encoding="utf-8")

    problem = parse_problem_html(
        html,
        source_url="https://3.shkolkovo.online/problem/100604?SubjectId=1",
    )

    assert problem.source_image_urls == (
        "https://3.shkolkovo.online/media/problems/100604/triangle.png",
        "https://static.shkolkovo.online/problems/100604/angle.png",
    )
    assert all("solution" not in url for url in problem.source_image_urls)


def test_problem_parser_extracts_source_id_from_url_when_page_has_no_id() -> None:
    html = """
    <html>
      <body>
        <section class="problem-text">Найдите значение выражения.</section>
        <span class="correct-answer">42</span>
      </body>
    </html>
    """

    problem = parse_problem_html(
        html,
        source_url="https://3.shkolkovo.online/problem/987654?SubjectId=1",
    )

    assert problem.source_id == "987654"


def test_problem_parser_returns_null_source_id_when_not_available() -> None:
    html = """
    <html>
      <body>
        <section class="problem-text">Найдите значение выражения.</section>
        <span class="correct-answer">42</span>
      </body>
    </html>
    """

    problem = parse_problem_html(html, source_url="https://example.test/no-id")

    assert problem.source_id is None


def test_source_id_from_url_supports_problem_path_and_common_query_keys() -> None:
    assert source_id_from_url("https://3.shkolkovo.online/problem/100601") == "100601"
    assert source_id_from_url("https://example.test/page?problem_id=100602") == "100602"
    assert source_id_from_url("https://example.test/page?id=100603") == "100603"
    assert source_id_from_url("https://example.test/page") is None

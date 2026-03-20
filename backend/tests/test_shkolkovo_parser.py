"""Tests for the Shkolkovo parser.

Tests the parsing logic using mock HTML without hitting the live site.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add tools directory to path so we can import the parser
_tools_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "parsers"
sys.path.insert(0, str(_tools_dir))

from bs4 import BeautifulSoup  # noqa: E402, I001
from shkolkovo_parser import (  # noqa: E402
    ParsedProblem,
    extract_answer,
    extract_images,
    extract_text_with_latex,
    parse_catalog_page,
    parse_problem_page,
    save_to_json,
    scrape_task,
)


# ---------------------------------------------------------------------------
# Fixtures: sample HTML fragments
# ---------------------------------------------------------------------------

SAMPLE_PROBLEM_HTML = """
<html>
<head><title>Задание 6 — Школково</title></head>
<body>
<main>
  <div class="task-content">
    <p>Найдите значение выражения \\( \\frac{2x+1}{x-3} \\) при \\( x = 5 \\).</p>
    <img src="/uploads/problems/task6_fig1.png" width="300" height="200" />
  </div>
  <div class="answer">Ответ: 5.5</div>
</main>
</body>
</html>
"""

SAMPLE_CATALOG_HTML = """
<html>
<body>
<div class="catalog-list">
  <a class="task-link" href="/task/12345">Задание 1</a>
  <a class="task-link" href="/task/12346">Задание 2</a>
  <a class="task-link" href="/task/12347">Задание 3</a>
</div>
<div class="pagination">
  <a class="next" href="/catalog/mathematics/zadanie-6-ege/?page=2">Далее</a>
</div>
</body>
</html>
"""

SAMPLE_PROBLEM_WITH_MATHJAX = """
<html>
<body>
<main>
  <div class="task-content">
    <p>Решите уравнение \\( x^2 - 4x + 3 = 0 \\).</p>
    <p>Если уравнение имеет более одного корня, в ответе запишите больший.</p>
  </div>
  <div class="answer">3</div>
</main>
</body>
</html>
"""

SAMPLE_PROBLEM_NO_ANSWER = """
<html>
<body>
<main>
  <div class="task-content">
    <p>Найдите площадь треугольника ABC.</p>
  </div>
</main>
</body>
</html>
"""

SAMPLE_CATALOG_NO_NEXT = """
<html>
<body>
<div class="catalog-list">
  <a class="task-link" href="/task/99999">Единственная задача</a>
</div>
</body>
</html>
"""

SAMPLE_PROBLEM_DISPLAY_MATH = """
<html>
<body>
<main>
  <div class="task-content">
    <p>Вычислите:</p>
    <p>\\[ \\int_0^1 x^2 dx \\]</p>
  </div>
  <div class="task-answer">Ответ: 0.333</div>
</main>
</body>
</html>
"""

SAMPLE_PROBLEM_DATA_ANSWER = """
<html>
<body>
<main>
  <div class="task-content" data-answer="42">
    <p>Найдите ответ на главный вопрос жизни.</p>
  </div>
</main>
</body>
</html>
"""

SAMPLE_CATALOG_FALLBACK_LINKS = """
<html>
<body>
<div class="content">
  <a href="/task/10001">Задача 1</a>
  <a href="/problem/10002">Задача 2</a>
  <a href="/about">О сайте</a>
  <a href="/exercise/10003">Задача 3</a>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Tests: extract_text_with_latex
# ---------------------------------------------------------------------------


class TestExtractTextWithLatex:
    def test_basic_text(self):
        soup = BeautifulSoup("<p>Hello world</p>", "lxml")
        result = extract_text_with_latex(soup)
        assert "Hello world" in result

    def test_mathjax_inline(self):
        soup = BeautifulSoup(
            r"<p>Найдите \( x^2 + 1 \)</p>", "lxml"
        )
        result = extract_text_with_latex(soup)
        assert "$" in result
        assert "x^2 + 1" in result

    def test_mathjax_display(self):
        soup = BeautifulSoup(
            r"<p>\[ \frac{a}{b} \]</p>", "lxml"
        )
        result = extract_text_with_latex(soup)
        assert "$$" in result
        assert r"\frac{a}{b}" in result

    def test_strips_script_tags(self):
        soup = BeautifulSoup(
            "<p>Text</p><script>evil()</script>", "lxml"
        )
        result = extract_text_with_latex(soup)
        assert "evil" not in result
        assert "Text" in result

    def test_none_input(self):
        result = extract_text_with_latex(None)
        assert result == ""


# ---------------------------------------------------------------------------
# Tests: extract_images
# ---------------------------------------------------------------------------


class TestExtractImages:
    def test_extracts_images(self):
        soup = BeautifulSoup(
            '<div><img src="/img/problem1.png" width="300" height="200" /></div>',
            "lxml",
        )
        images = extract_images(soup)
        assert len(images) == 1
        assert images[0] == "https://3.shkolkovo.online/img/problem1.png"

    def test_skips_tiny_images(self):
        soup = BeautifulSoup(
            '<div><img src="/pixel.gif" width="1" height="1" /></div>',
            "lxml",
        )
        images = extract_images(soup)
        assert len(images) == 0

    def test_handles_absolute_urls(self):
        html = (
            '<div><img src="https://cdn.example.com/img.png"'
            ' width="100" height="100" /></div>'
        )
        soup = BeautifulSoup(html, "lxml")
        images = extract_images(soup)
        assert images[0] == "https://cdn.example.com/img.png"

    def test_handles_protocol_relative(self):
        html = (
            '<div><img src="//cdn.example.com/img.png"'
            ' width="100" height="100" /></div>'
        )
        soup = BeautifulSoup(html, "lxml")
        images = extract_images(soup)
        assert images[0] == "https://cdn.example.com/img.png"

    def test_none_input(self):
        assert extract_images(None) == []


# ---------------------------------------------------------------------------
# Tests: extract_answer
# ---------------------------------------------------------------------------


class TestExtractAnswer:
    def test_answer_class(self):
        soup = BeautifulSoup(
            '<div><div class="answer">Ответ: 42</div></div>', "lxml"
        )
        assert extract_answer(soup) == "42"

    def test_task_answer_class(self):
        soup = BeautifulSoup(
            '<div><div class="task-answer">Ответ: 3.14</div></div>', "lxml"
        )
        assert extract_answer(soup) == "3.14"

    def test_data_answer_attribute(self):
        soup = BeautifulSoup(
            '<div data-answer="7"><p>Problem text</p></div>', "lxml"
        )
        assert extract_answer(soup) == "7"

    def test_answer_in_text(self):
        soup = BeautifulSoup(
            '<div><p>Some solution text.</p><p>Ответ: 99</p></div>', "lxml"
        )
        assert extract_answer(soup) == "99"

    def test_no_answer(self):
        soup = BeautifulSoup(
            "<div><p>Just a problem</p></div>", "lxml"
        )
        assert extract_answer(soup) is None

    def test_none_input(self):
        assert extract_answer(None) is None


# ---------------------------------------------------------------------------
# Tests: ParsedProblem
# ---------------------------------------------------------------------------


class TestParsedProblem:
    def test_compute_hash_deterministic(self):
        p1 = ParsedProblem(task_number=6, problem_text="Find x + 1")
        p2 = ParsedProblem(task_number=6, problem_text="Find x + 1")
        p1.compute_hash()
        p2.compute_hash()
        assert p1.content_hash == p2.content_hash
        assert len(p1.content_hash) == 64

    def test_compute_hash_ignores_whitespace(self):
        p1 = ParsedProblem(task_number=6, problem_text="Find  x  + 1")
        p2 = ParsedProblem(task_number=6, problem_text="Find x + 1")
        p1.compute_hash()
        p2.compute_hash()
        assert p1.content_hash == p2.content_hash

    def test_different_text_different_hash(self):
        p1 = ParsedProblem(task_number=6, problem_text="Problem A")
        p2 = ParsedProblem(task_number=6, problem_text="Problem B")
        p1.compute_hash()
        p2.compute_hash()
        assert p1.content_hash != p2.content_hash

    def test_default_values(self):
        p = ParsedProblem(task_number=7, problem_text="text")
        assert p.source == "shkolkovo"
        assert p.difficulty == "medium"
        assert p.problem_images == []
        assert p.correct_answer is None


# ---------------------------------------------------------------------------
# Tests: parse_problem_page (mocked HTTP)
# ---------------------------------------------------------------------------


class TestParseProblemPage:
    def _mock_session(self, html: str) -> MagicMock:
        session = MagicMock()
        resp = MagicMock()
        resp.text = html
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        session.get.return_value = resp
        return session

    def test_parses_problem_with_latex(self):
        session = self._mock_session(SAMPLE_PROBLEM_HTML)
        problem = parse_problem_page("https://example.com/task/1", 6, session)
        assert problem is not None
        assert problem.task_number == 6
        assert "$" in problem.problem_text
        assert "5.5" == problem.correct_answer
        assert problem.content_hash
        assert len(problem.problem_images) == 1

    def test_parses_mathjax_delimiters(self):
        session = self._mock_session(SAMPLE_PROBLEM_WITH_MATHJAX)
        problem = parse_problem_page("https://example.com/task/2", 7, session)
        assert problem is not None
        assert "x^2 - 4x + 3 = 0" in problem.problem_text
        assert problem.correct_answer == "3"

    def test_parses_display_math(self):
        session = self._mock_session(SAMPLE_PROBLEM_DISPLAY_MATH)
        problem = parse_problem_page("https://example.com/task/3", 13, session)
        assert problem is not None
        assert "$$" in problem.problem_text
        assert problem.correct_answer == "0.333"

    def test_handles_no_answer(self):
        session = self._mock_session(SAMPLE_PROBLEM_NO_ANSWER)
        problem = parse_problem_page("https://example.com/task/4", 6, session)
        assert problem is not None
        assert problem.correct_answer is None

    def test_handles_network_error(self):
        session = MagicMock()
        session.get.side_effect = Exception("Network error")
        problem = parse_problem_page("https://example.com/task/5", 6, session)
        assert problem is None

    def test_source_url_set(self):
        session = self._mock_session(SAMPLE_PROBLEM_HTML)
        url = "https://example.com/task/123"
        problem = parse_problem_page(url, 6, session)
        assert problem is not None
        assert problem.source_url == url


# ---------------------------------------------------------------------------
# Tests: parse_catalog_page
# ---------------------------------------------------------------------------


class TestParseCatalogPage:
    def _mock_session(self, html: str) -> MagicMock:
        session = MagicMock()
        resp = MagicMock()
        resp.text = html
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        session.get.return_value = resp
        return session

    def test_extracts_problem_links(self):
        session = self._mock_session(SAMPLE_CATALOG_HTML)
        urls, next_url = parse_catalog_page(
            "https://3.shkolkovo.online/catalog/mathematics/zadanie-6-ege/",
            6,
            session,
        )
        assert len(urls) == 3
        assert all("3.shkolkovo.online" in u for u in urls)

    def test_extracts_next_page(self):
        session = self._mock_session(SAMPLE_CATALOG_HTML)
        _, next_url = parse_catalog_page(
            "https://3.shkolkovo.online/catalog/mathematics/zadanie-6-ege/",
            6,
            session,
        )
        assert next_url is not None
        assert "page=2" in next_url

    def test_no_next_page(self):
        session = self._mock_session(SAMPLE_CATALOG_NO_NEXT)
        urls, next_url = parse_catalog_page(
            "https://3.shkolkovo.online/catalog/mathematics/zadanie-6-ege/",
            6,
            session,
        )
        assert len(urls) == 1
        assert next_url is None

    def test_fallback_link_detection(self):
        session = self._mock_session(SAMPLE_CATALOG_FALLBACK_LINKS)
        urls, _ = parse_catalog_page(
            "https://3.shkolkovo.online/catalog/mathematics/zadanie-6-ege/",
            6,
            session,
        )
        # Should find /task/10001, /problem/10002, /exercise/10003 but not /about
        assert len(urls) == 3
        assert all("/about" not in u for u in urls)

    def test_handles_network_error(self):
        session = MagicMock()
        session.get.side_effect = Exception("Network error")
        urls, next_url = parse_catalog_page("https://example.com", 6, session)
        assert urls == []
        assert next_url is None


# ---------------------------------------------------------------------------
# Tests: scrape_task (integration with mocks)
# ---------------------------------------------------------------------------


class TestScrapeTask:
    def test_invalid_task_number(self):
        result = scrape_task(0)
        assert result == []
        result = scrape_task(20)
        assert result == []

    @patch("shkolkovo_parser.time.sleep")
    @patch("shkolkovo_parser.fetch_page")
    def test_scrape_collects_problems(self, mock_fetch, mock_sleep):
        catalog_soup = BeautifulSoup(SAMPLE_CATALOG_NO_NEXT, "lxml")
        problem_soup = BeautifulSoup(SAMPLE_PROBLEM_HTML, "lxml")

        mock_fetch.side_effect = [catalog_soup, problem_soup]

        result = scrape_task(6, max_pages=1, max_problems=5)
        assert len(result) >= 1
        assert result[0].task_number == 6
        assert result[0].source == "shkolkovo"

    @patch("shkolkovo_parser.time.sleep")
    @patch("shkolkovo_parser.fetch_page")
    def test_deduplication(self, mock_fetch, mock_sleep):
        catalog_html = """
        <html><body>
        <div class="catalog-list">
          <a class="task-link" href="/task/1">T1</a>
          <a class="task-link" href="/task/2">T2</a>
        </div>
        </body></html>
        """
        catalog_soup = BeautifulSoup(catalog_html, "lxml")
        # Return the same problem HTML for both links
        problem_soup = BeautifulSoup(SAMPLE_PROBLEM_HTML, "lxml")

        mock_fetch.side_effect = [catalog_soup, problem_soup, problem_soup]

        result = scrape_task(6, max_pages=1, max_problems=5)
        # Should deduplicate — only 1 unique problem
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Tests: save_to_json
# ---------------------------------------------------------------------------


class TestSaveToJson:
    def test_saves_valid_json(self, tmp_path):
        problems = [
            ParsedProblem(
                task_number=6,
                problem_text="Find x",
                correct_answer="5",
                content_hash="abc123",
                source_url="https://example.com/1",
            ),
            ParsedProblem(
                task_number=6,
                problem_text="Find y",
                correct_answer="10",
                content_hash="def456",
                source_url="https://example.com/2",
            ),
        ]

        out_file = str(tmp_path / "test_output.json")
        save_to_json(problems, out_file)

        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["task_number"] == 6
        assert data[0]["source"] == "shkolkovo"
        assert data[0]["content_hash"] == "abc123"
        assert data[1]["correct_answer"] == "10"

    def test_handles_unicode(self, tmp_path):
        problems = [
            ParsedProblem(
                task_number=1,
                problem_text="Найдите значение выражения $x^2$",
                content_hash="hash1",
            ),
        ]

        out_file = str(tmp_path / "unicode_output.json")
        save_to_json(problems, out_file)

        with open(out_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "Найдите" in data[0]["problem_text"]
        assert "$x^2$" in data[0]["problem_text"]

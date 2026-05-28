"""Parser for public Shkolkovo problem pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup, Tag

PROBLEM_ID_PATTERN = re.compile(r"/problem/(\d+)(?:\D|$)")


@dataclass(frozen=True)
class ParsedProblem:
    """Problem data extracted from one public problem page."""

    problem_text: str
    correct_answer: str | None
    source_url: str
    source_id: str | None


def parse_problem_html(html: str, *, source_url: str | None = None) -> ParsedProblem:
    """Extract problem text, public answer, and source metadata from HTML."""
    soup = BeautifulSoup(html, "lxml")
    source_url = source_url or _first_attr(soup, "data-source-url") or ""
    return ParsedProblem(
        problem_text=_extract_problem_text(soup),
        correct_answer=_extract_correct_answer(soup),
        source_url=source_url,
        source_id=_extract_source_id(soup, source_url),
    )


def _extract_problem_text(soup: BeautifulSoup) -> str:
    problem_node = soup.select_one(".problem-text")
    if problem_node is None:
        return ""
    return _normalized_text(problem_node)


def _extract_correct_answer(soup: BeautifulSoup) -> str | None:
    answer_node = soup.select_one(".correct-answer")
    if answer_node is None:
        return None
    answer = _normalized_text(answer_node)
    return answer or None


def _extract_source_id(soup: BeautifulSoup, source_url: str) -> str | None:
    source_id = _first_attr(soup, "data-source-id")
    if source_id:
        return source_id
    return source_id_from_url(source_url)


def source_id_from_url(source_url: str) -> str | None:
    """Extract a public Shkolkovo source id from a problem URL if present."""
    parsed_url = urlparse(source_url)
    match = PROBLEM_ID_PATTERN.search(parsed_url.path)
    if match is not None:
        return match.group(1)

    query_values = parse_qs(parsed_url.query)
    for query_key in ("problem", "problem_id", "id"):
        values = query_values.get(query_key)
        if values and values[0].isdigit():
            return values[0]
    return None


def _first_attr(soup: BeautifulSoup, attr_name: str) -> str | None:
    node = soup.find(attrs={attr_name: True})
    if not isinstance(node, Tag):
        return None
    value = node.get(attr_name)
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _normalized_text(node: Tag) -> str:
    return " ".join(node.get_text(" ", strip=True).split())

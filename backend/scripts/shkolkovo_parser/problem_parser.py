"""Parser for public Shkolkovo problem pages."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from scripts.shkolkovo_parser.normalizer import (
    normalize_plain_text,
    normalize_problem_text,
)

PROBLEM_ID_PATTERN = re.compile(r"/problem/(\d+)(?:\D|$)")


@dataclass(frozen=True)
class ParsedProblem:
    """Problem data extracted from one public problem page."""

    problem_text: str
    correct_answer: str | None
    source_url: str
    source_id: str | None
    source_image_urls: tuple[str, ...] = ()


def parse_problem_html(html: str, *, source_url: str | None = None) -> ParsedProblem:
    """Extract problem text, public answer, and source metadata from HTML."""
    soup = BeautifulSoup(html, "lxml")
    source_url = source_url or _first_attr(soup, "data-source-url") or ""
    return ParsedProblem(
        problem_text=_extract_problem_text(soup),
        correct_answer=_extract_correct_answer(soup),
        source_url=source_url,
        source_id=_extract_source_id(soup, source_url),
        source_image_urls=_extract_source_image_urls(soup, source_url),
    )


def _extract_problem_text(soup: BeautifulSoup) -> str:
    problem_node = soup.select_one(".problem-text")
    if problem_node is None:
        return ""
    return normalize_problem_text(problem_node)


def _extract_correct_answer(soup: BeautifulSoup) -> str | None:
    answer_node = soup.select_one(".correct-answer")
    if answer_node is None:
        return None
    answer = normalize_plain_text(answer_node)
    return answer or None


def _extract_source_image_urls(
    soup: BeautifulSoup,
    source_url: str,
) -> tuple[str, ...]:
    problem_node = soup.select_one(".problem-text")
    if problem_node is None:
        return ()

    image_urls: list[str] = []
    seen: set[str] = set()
    for image_node in problem_node.select("img"):
        for raw_url in _candidate_image_urls(image_node):
            absolute_url = _absolute_http_url(raw_url, source_url)
            if absolute_url is None or absolute_url in seen:
                continue
            seen.add(absolute_url)
            image_urls.append(absolute_url)
    return tuple(image_urls)


def _candidate_image_urls(image_node: Tag) -> tuple[str, ...]:
    urls: list[str] = []
    for attr_name in ("src", "data-src", "data-original", "data-lazy-src"):
        value = image_node.get(attr_name)
        if isinstance(value, str) and value.strip():
            urls.append(value.strip())

    for attr_name in ("srcset", "data-srcset"):
        value = image_node.get(attr_name)
        if not isinstance(value, str):
            continue
        urls.extend(_urls_from_srcset(value))
    return tuple(urls)


def _urls_from_srcset(srcset: str) -> tuple[str, ...]:
    urls: list[str] = []
    for candidate in srcset.split(","):
        url = candidate.strip().split(maxsplit=1)[0]
        if url:
            urls.append(url)
    return tuple(urls)


def _absolute_http_url(raw_url: str, source_url: str) -> str | None:
    if raw_url.startswith(("#", "data:", "blob:", "javascript:")):
        return None
    absolute_url = urljoin(source_url, raw_url)
    parsed_url = urlparse(absolute_url)
    if parsed_url.scheme not in {"http", "https"}:
        return None
    return absolute_url


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

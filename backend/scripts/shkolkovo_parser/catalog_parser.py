"""Parser for public Shkolkovo catalog pages."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from scripts.shkolkovo_parser.problem_parser import source_id_from_url

DEFAULT_CATALOG_BASE_URL = "https://3.shkolkovo.online/catalog?SubjectId=1"
MIN_TASK_NUMBER = 1
MAX_TASK_NUMBER = 19


@dataclass(frozen=True)
class CatalogProblemLink:
    """Problem link discovered in a catalog page."""

    source_url: str
    task_number: int
    category: str | None
    subcategory: str | None
    source_id: str | None


@dataclass(frozen=True)
class CatalogParseError:
    """Diagnostic for a catalog link that cannot become a dataset candidate."""

    source_url: str | None
    reason: str
    message: str


@dataclass(frozen=True)
class ParsedCatalog:
    """Catalog parser output with usable problem links and rejected entries."""

    problems: tuple[CatalogProblemLink, ...]
    errors: tuple[CatalogParseError, ...]


def parse_catalog_html(
    html: str,
    *,
    base_url: str = DEFAULT_CATALOG_BASE_URL,
) -> ParsedCatalog:
    """Extract public problem links and their catalog classification."""
    soup = BeautifulSoup(html, "lxml")
    problems: list[CatalogProblemLink] = []
    errors: list[CatalogParseError] = []

    for link in soup.select("a.problem-link[href]"):
        if not isinstance(link, Tag):
            continue

        source_url = _absolute_url(link, base_url)
        task_number, task_error = _task_number_for_link(link)
        if task_error is not None:
            errors.append(
                CatalogParseError(
                    source_url=source_url,
                    reason=task_error,
                    message=_error_message(task_error),
                ),
            )
            continue

        problems.append(
            CatalogProblemLink(
                source_url=source_url,
                task_number=task_number,
                category=_closest_attr(link, ".catalog-category", "data-category"),
                subcategory=_closest_attr(
                    link,
                    ".catalog-subcategory",
                    "data-subcategory",
                ),
                source_id=_source_id(link, source_url),
            ),
        )

    return ParsedCatalog(problems=tuple(problems), errors=tuple(errors))


def _absolute_url(link: Tag, base_url: str) -> str:
    href = link.get("href")
    return urljoin(base_url, href.strip() if isinstance(href, str) else "")


def _task_number_for_link(link: Tag) -> tuple[int, str | None]:
    task_node = link.find_parent(class_="catalog-task")
    if not isinstance(task_node, Tag):
        return 0, "missing_task_number"

    raw_task_number = task_node.get("data-task-number")
    if not isinstance(raw_task_number, str) or not raw_task_number.strip():
        return 0, "missing_task_number"

    try:
        task_number = int(raw_task_number)
    except ValueError:
        return 0, "invalid_task_number"

    if not MIN_TASK_NUMBER <= task_number <= MAX_TASK_NUMBER:
        return task_number, "task_number_out_of_range"
    return task_number, None


def _closest_attr(link: Tag, selector: str, attr_name: str) -> str | None:
    node = link.find_parent(class_=selector.removeprefix("."))
    if not isinstance(node, Tag):
        return None

    value = node.get(attr_name)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _source_id(link: Tag, source_url: str) -> str | None:
    source_id = link.get("data-source-id")
    if isinstance(source_id, str) and source_id.strip():
        return source_id.strip()
    return source_id_from_url(source_url)


def _error_message(reason: str) -> str:
    if reason == "missing_task_number":
        return "catalog problem link has no task number context"
    if reason == "invalid_task_number":
        return "catalog problem link has a non-integer task number"
    if reason == "task_number_out_of_range":
        return (
            f"catalog problem link task number is outside "
            f"{MIN_TASK_NUMBER}-{MAX_TASK_NUMBER}"
        )
    return "catalog problem link is invalid"

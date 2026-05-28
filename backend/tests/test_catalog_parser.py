"""Tests for parsing Shkolkovo catalog pages."""

from __future__ import annotations

from pathlib import Path

from scripts.shkolkovo_parser.catalog_parser import (
    CatalogProblemLink,
    parse_catalog_html,
)

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "shkolkovo"


def test_catalog_parser_extracts_problem_links_and_classification() -> None:
    html = (FIXTURE_DIR / "catalog_task_6.html").read_text(encoding="utf-8")

    catalog = parse_catalog_html(html)

    assert catalog.problems == (
        CatalogProblemLink(
            source_url="https://3.shkolkovo.online/problem/100601?SubjectId=1",
            task_number=6,
            category="Планиметрия",
            subcategory="Треугольники",
            source_id="100601",
        ),
        CatalogProblemLink(
            source_url="https://3.shkolkovo.online/problem/100602?SubjectId=1",
            task_number=6,
            category="Планиметрия",
            subcategory="Треугольники",
            source_id="100602",
        ),
        CatalogProblemLink(
            source_url="https://3.shkolkovo.online/problem/100603?SubjectId=1",
            task_number=6,
            category="Планиметрия",
            subcategory="Окружности",
            source_id="100603",
        ),
    )


def test_catalog_parser_rejects_links_with_out_of_range_task_number() -> None:
    html = (FIXTURE_DIR / "catalog_task_6.html").read_text(encoding="utf-8")

    catalog = parse_catalog_html(html)

    assert len(catalog.problems) == 3
    assert len(catalog.errors) == 1
    assert catalog.errors[0].reason == "task_number_out_of_range"
    assert catalog.errors[0].source_url == (
        "https://3.shkolkovo.online/problem/200001?SubjectId=1"
    )


def test_catalog_parser_rejects_problem_link_without_task_number() -> None:
    html = """
    <html>
      <body>
        <main>
          <a class="problem-link" href="/problem/100604?SubjectId=1">
            Missing task context
          </a>
        </main>
      </body>
    </html>
    """

    catalog = parse_catalog_html(html)

    assert catalog.problems == ()
    assert len(catalog.errors) == 1
    assert catalog.errors[0].reason == "missing_task_number"
    assert catalog.errors[0].source_url == (
        "https://3.shkolkovo.online/problem/100604?SubjectId=1"
    )


def test_catalog_parser_uses_base_url_and_source_id_from_url() -> None:
    html = """
    <html>
      <body>
        <section class="catalog-task" data-task-number="6">
          <section class="catalog-category" data-category="Категория">
            <article class="catalog-subcategory" data-subcategory="Подтип">
              <a class="problem-link" href="problem/100605?SubjectId=1">
                Relative link without explicit source id
              </a>
            </article>
          </section>
        </section>
      </body>
    </html>
    """

    catalog = parse_catalog_html(
        html,
        base_url="https://example.test/catalog/page/1",
    )

    assert catalog.problems == (
        CatalogProblemLink(
            source_url="https://example.test/catalog/page/problem/100605?SubjectId=1",
            task_number=6,
            category="Категория",
            subcategory="Подтип",
            source_id="100605",
        ),
    )
    assert catalog.errors == ()

#!/usr/bin/env python3
"""Bulk import problems from parser JSON into the Supabase problems table.

Usage:
    cd backend
    python -m scripts.import_problems path/to/problems.json
    python -m scripts.import_problems ../data/raw/shkolkovo

JSON format — array of objects:
[
  {
    "task_number": 1,          # required, 1-19
    "problem_text": "...",     # required
    "correct_answer": "5",     # required for Part 1 (tasks 1-12)
    "difficulty": "medium",    # optional, default "medium"
    "answer_tolerance": 0,     # optional, default 0
    "solution_markdown": "...",# optional
    "hints": ["..."],          # optional
    "problem_images": ["..."], # optional, parser local/Supabase image refs
    "source": "ФИПИ",          # optional
    "source_id": "123",        # optional
    "source_url": "https://...", # optional
    "content_hash": "..."      # optional, preferred dedup key
  }
]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client

VALID_DIFFICULTIES = {"basic", "medium", "hard", "olympiad"}
REQUIRED_FIELDS = {"task_number", "problem_text"}
JSON_LIST_FIELDS = {
    "hints",
    "problem_images",
    "solution_images",
    "source_image_urls",
    "parse_errors",
}
PARSER_TASK_GLOB = "task_*.json"


def _load_json(path: str) -> list[dict]:
    file_path = Path(path)
    if not file_path.exists():
        print(f"Ошибка: файл не найден: {path}")
        sys.exit(1)
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("Ошибка: JSON должен быть массивом объектов")
        sys.exit(1)
    return data


def _json_files(path: str) -> list[Path]:
    """Return parser JSON files for a file or directory input."""
    input_path = Path(path)
    if not input_path.exists():
        print(f"Ошибка: путь не найден: {path}")
        sys.exit(1)

    if input_path.is_file():
        return [input_path]

    files = [
        file_path
        for file_path in sorted(input_path.glob(PARSER_TASK_GLOB))
        if not file_path.name.endswith("_errors.json")
        and not file_path.name.endswith("_report.json")
    ]
    if not files:
        print(f"Ошибка: в директории нет файлов {PARSER_TASK_GLOB}: {path}")
        sys.exit(1)
    return files


def _load_items(path: str) -> list[dict]:
    """Load one JSON file or all task_N.json files from a parser directory."""
    items: list[dict] = []
    for file_path in _json_files(path):
        items.extend(_load_json(str(file_path)))
    return items


def _validate(item: dict, index: int) -> list[str]:
    """Return list of validation errors for a single problem."""
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if not item.get(field):
            errors.append(
                f"[{index}] отсутствует обязательное поле"
                f" '{field}'"
            )

    task_number = item.get("task_number")
    if isinstance(task_number, int) and not (1 <= task_number <= 19):
        errors.append(
            f"[{index}] task_number={task_number}"
            " вне диапазона 1-19"
        )

    # Part 1 (tasks 1-12) requires correct_answer
    if isinstance(task_number, int) and 1 <= task_number <= 12:
        if not item.get("correct_answer"):
            errors.append(
                f"[{index}] correct_answer обязателен"
                f" для Части 1 (task_number={task_number})"
            )

    difficulty = item.get("difficulty", "medium")
    if difficulty not in VALID_DIFFICULTIES:
        errors.append(
            f"[{index}] difficulty='{difficulty}'"
            f" не в {VALID_DIFFICULTIES}"
        )

    for field in JSON_LIST_FIELDS:
        value = item.get(field)
        if value is not None and not isinstance(value, list):
            errors.append(f"[{index}] '{field}' должен быть массивом")

    return errors


def _is_parser_partial_without_answer(item: dict) -> bool:
    """Whether a parser-produced Part 1 row is displayable but unsolvable."""
    task_number = item.get("task_number")
    if not isinstance(task_number, int) or task_number > 12:
        return False
    parse_errors = item.get("parse_errors")
    return (
        item.get("parse_status") == "partial"
        and isinstance(parse_errors, list)
        and "missing_correct_answer" in parse_errors
        and not item.get("correct_answer")
    )


def _get_topic_map(client: Client) -> dict[int, str]:
    """Fetch mapping task_number -> topic_id."""
    result = (
        client.table("topics")
        .select("id, task_number")
        .execute()
    )
    return {
        row["task_number"]: row["id"] for row in result.data
    }


def _get_existing_texts(
    client: Client, topic_ids: set[str]
) -> set[str]:
    """Fetch existing problem_text values for dedup."""
    if not topic_ids:
        return set()
    result = (
        client.table("problems")
        .select("problem_text")
        .in_("topic_id", list(topic_ids))
        .execute()
    )
    return {row["problem_text"].strip() for row in result.data}


def _get_existing_problem_keys(
    client: Client, topic_ids: set[str]
) -> tuple[set[str], set[str]]:
    """Fetch existing problem text and content hashes for deduplication."""
    if not topic_ids:
        return set(), set()
    result = (
        client.table("problems")
        .select("problem_text,content_hash")
        .in_("topic_id", list(topic_ids))
        .execute()
    )
    texts: set[str] = set()
    hashes: set[str] = set()
    for row in result.data or []:
        if row.get("problem_text"):
            texts.add(row["problem_text"].strip())
        if row.get("content_hash"):
            hashes.add(row["content_hash"])
    return texts, hashes


def _list_field(item: dict, field: str) -> list:
    value = item.get(field)
    return value if isinstance(value, list) else []


def _optional_text(item: dict, field: str) -> str | None:
    value = item.get(field)
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _build_problem_row(item: dict, *, topic_id: str, problem_text: str) -> dict:
    row = {
        "topic_id": topic_id,
        "task_number": item["task_number"],
        "difficulty": item.get("difficulty", "medium"),
        "problem_text": problem_text,
        "problem_images": _list_field(item, "problem_images"),
        "correct_answer": _optional_text(item, "correct_answer"),
        "answer_tolerance": item.get("answer_tolerance", 0),
        "solution_markdown": _optional_text(item, "solution_markdown"),
        "solution_images": _list_field(item, "solution_images"),
        "hints": _list_field(item, "hints"),
        "source": _optional_text(item, "source"),
        "source_url": _optional_text(item, "source_url"),
        "source_id": _optional_text(item, "source_id"),
        "content_hash": _optional_text(item, "content_hash"),
        "category": _optional_text(item, "category"),
        "subcategory": _optional_text(item, "subcategory"),
        "source_image_urls": _list_field(item, "source_image_urls"),
        "parse_status": item.get("parse_status") or "ok",
        "parse_errors": _list_field(item, "parse_errors"),
    }
    if prototype_id := _optional_text(item, "prototype_id"):
        row["prototype_id"] = prototype_id
    return row


def import_problems(
    json_path: str, *, client: Client | None = None
) -> None:
    """Import problems from a parser JSON file or parser output directory.

    Args:
        json_path: Path to JSON file or directory with task_N.json files.
        client: Supabase client. If None, creates one from
                app settings.
    """
    items = _load_items(json_path)
    if not items:
        print("Файлы пустые — нечего импортировать.")
        return

    # Validate all items first
    all_errors: list[str] = []
    partial_without_answer: set[int] = set()
    for i, item in enumerate(items):
        item_errors = _validate(item, i)
        if _is_parser_partial_without_answer(item):
            answer_errors = [err for err in item_errors if "correct_answer" in err]
            other_errors = [err for err in item_errors if "correct_answer" not in err]
            if answer_errors and not other_errors:
                partial_without_answer.add(i)
                continue
        all_errors.extend(item_errors)

    if all_errors:
        print(f"Ошибки валидации ({len(all_errors)}):")
        for err in all_errors:
            print(f"  {err}")
        sys.exit(1)

    # Connect to Supabase if no client provided
    if client is None:
        from supabase import create_client

        from app.core.config import settings

        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY,
        )

    # Build topic_number -> topic_id map
    topic_map = _get_topic_map(client)
    needed_tasks = {item["task_number"] for item in items}
    missing_tasks = needed_tasks - set(topic_map.keys())
    if missing_tasks:
        print(
            "Ошибка: в БД нет тем для task_number:"
            f" {sorted(missing_tasks)}"
        )
        sys.exit(1)

    # Fetch existing problem identities for deduplication
    relevant_topic_ids = {topic_map[tn] for tn in needed_tasks}
    existing_texts, existing_hashes = _get_existing_problem_keys(
        client, relevant_topic_ids
    )

    added = 0
    skipped = 0
    skipped_partial = 0
    errors = 0

    for i, item in enumerate(items):
        if i in partial_without_answer:
            skipped_partial += 1
            continue

        text = item["problem_text"].strip()
        content_hash = _optional_text(item, "content_hash")
        if (content_hash and content_hash in existing_hashes) or text in existing_texts:
            skipped += 1
            continue

        topic_id = topic_map[item["task_number"]]
        row = _build_problem_row(item, topic_id=topic_id, problem_text=text)

        try:
            client.table("problems").insert(row).execute()
            existing_texts.add(text)
            if content_hash:
                existing_hashes.add(content_hash)
            added += 1
        except Exception as e:
            print(f"  Ошибка вставки [{i}]: {e}")
            errors += 1

    print(
        f"Добавлено: {added},"
        f" Пропущено (дубликаты): {skipped},"
        f" Пропущено (неполные): {skipped_partial},"
        f" Ошибки: {errors}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Использование:"
            " python -m scripts.import_problems"
            " <path/to/problems.json|data/raw/shkolkovo>"
        )
        sys.exit(1)
    import_problems(sys.argv[1])


if __name__ == "__main__":
    main()

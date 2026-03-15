#!/usr/bin/env python3
"""Bulk import problems from a JSON file into the Supabase problems table.

Usage:
    cd backend
    python -m scripts.import_problems path/to/problems.json

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
    "source": "ФИПИ"          # optional
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

    return errors


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


def import_problems(
    json_path: str, *, client: Client | None = None
) -> None:
    """Import problems from JSON file.

    Args:
        json_path: Path to JSON file with problems array.
        client: Supabase client. If None, creates one from
                app settings.
    """
    items = _load_json(json_path)
    if not items:
        print("Файл пуст — нечего импортировать.")
        return

    # Validate all items first
    all_errors: list[str] = []
    for i, item in enumerate(items):
        all_errors.extend(_validate(item, i))

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

    # Fetch existing problem texts for deduplication
    relevant_topic_ids = {topic_map[tn] for tn in needed_tasks}
    existing_texts = _get_existing_texts(
        client, relevant_topic_ids
    )

    added = 0
    skipped = 0
    errors = 0

    for i, item in enumerate(items):
        text = item["problem_text"].strip()
        if text in existing_texts:
            skipped += 1
            continue

        topic_id = topic_map[item["task_number"]]
        row = {
            "topic_id": topic_id,
            "task_number": item["task_number"],
            "difficulty": item.get("difficulty", "medium"),
            "problem_text": text,
            "correct_answer": item.get("correct_answer"),
            "answer_tolerance": item.get("answer_tolerance", 0),
            "solution_markdown": item.get("solution_markdown"),
            "hints": item.get("hints", []),
            "source": item.get("source"),
        }

        try:
            client.table("problems").insert(row).execute()
            existing_texts.add(text)
            added += 1
        except Exception as e:
            print(f"  Ошибка вставки [{i}]: {e}")
            errors += 1

    print(
        f"Добавлено: {added},"
        f" Пропущено (дубликаты): {skipped},"
        f" Ошибки: {errors}"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Использование:"
            " python -m scripts.import_problems"
            " <path/to/problems.json>"
        )
        sys.exit(1)
    import_problems(sys.argv[1])


if __name__ == "__main__":
    main()

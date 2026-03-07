#!/usr/bin/env python3
"""
Seed script: загружает карточки из JSON в Supabase.

Использование:
    python database/seeds/load_cards.py basic          # загрузит cards_basic.json
    python database/seeds/load_cards.py stepbystep     # загрузит cards_stepbystep.json
    python database/seeds/load_cards.py --file path/to/file.json

Требует переменных окружения:
    SUPABASE_URL              — URL проекта Supabase
    SUPABASE_SERVICE_ROLE_KEY — ключ с правами обхода RLS

Зависимости:
    pip install supabase python-dotenv
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    from supabase import Client, create_client
except ImportError as exc:
    print(
        f"[ERROR] Не установлены зависимости: {exc}\n"
        "Запустите: pip install supabase python-dotenv"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SEEDS_DIR = Path(__file__).parent
ENV_FILE = SEEDS_DIR.parent.parent / "backend" / ".env"

TYPE_TO_FILE: dict[str, str] = {
    "basic": "cards_basic.json",
    "stepbystep": "cards_stepbystep.json",
}


def load_env() -> None:
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    else:
        load_dotenv()


def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print(
            "[ERROR] Не заданы переменные окружения SUPABASE_URL и/или "
            "SUPABASE_SERVICE_ROLE_KEY"
        )
        sys.exit(1)
    return create_client(url, key)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def fetch_topic_code_to_id(client: Client) -> dict[str, str]:
    """Загружает все темы и возвращает словарь code → id."""
    response = client.table("topics").select("id, code").execute()
    if not response.data:
        print("[WARN] Таблица topics пуста. Сначала запустите load_topics.py.")
        return {}
    return {row["code"]: row["id"] for row in response.data}


def fetch_existing_keys(client: Client) -> set[tuple[str, str]]:
    """Возвращает множество (topic_id, question_text) уже существующих карточек."""
    response = client.table("cards").select("topic_id, question_text").execute()
    if not response.data:
        return set()
    return {(row["topic_id"], row["question_text"]) for row in response.data}


def load_cards(client: Client, cards_file: Path) -> None:
    with cards_file.open(encoding="utf-8") as f:
        data = json.load(f)

    cards: list[dict] = data["cards"]
    print(f"[INFO] Загружено {len(cards)} карточек из {cards_file.name}")

    code_to_id = fetch_topic_code_to_id(client)
    existing_keys = fetch_existing_keys(client)

    inserted = 0
    skipped = 0
    errors = 0

    for card in cards:
        topic_code = card.get("topic_code")
        question_text = card.get("question_text", "")

        # Resolve topic_id
        topic_id = code_to_id.get(topic_code) if topic_code else None
        if topic_id is None:
            print(f"  [ERROR] Тема '{topic_code}' не найдена — карточка пропущена.")
            errors += 1
            continue

        # Check for duplicates
        if (topic_id, question_text) in existing_keys:
            print(f"  [SKIP] '{question_text[:60]}...' — уже существует")
            skipped += 1
            continue

        row = {
            "topic_id": topic_id,
            "card_type": card.get("card_type", "basic_qa"),
            "question_text": question_text,
            "answer_text": card.get("answer_text", ""),
            "hints": card.get("hints", []),
            "difficulty": card.get("difficulty", 0.5),
        }

        ege_task_number = card.get("ege_task_number")
        if ege_task_number is not None:
            row["ege_task_number"] = ege_task_number

        solution_steps = card.get("solution_steps")
        if solution_steps is not None:
            row["solution_steps"] = solution_steps

        result = client.table("cards").insert(row).execute()
        if result.data:
            new_id: str = result.data[0]["id"]
            print(f"  [OK]   '{question_text[:60]}' (id={new_id[:8]}...)")
            existing_keys.add((topic_id, question_text))
            inserted += 1
        else:
            print(f"  [ERROR] '{question_text[:60]}' — ошибка вставки: {result}")
            errors += 1

    print(
        f"\n[DONE] Вставлено: {inserted}, пропущено: {skipped}, "
        f"ошибок: {errors}, всего в файле: {len(cards)}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Загрузка карточек в Supabase")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "card_type",
        nargs="?",
        choices=list(TYPE_TO_FILE.keys()),
        help="Тип карточек: basic или stepbystep",
    )
    group.add_argument(
        "--file",
        type=Path,
        help="Путь к JSON-файлу с карточками",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    load_env()
    client = get_supabase_client()

    if args.file:
        cards_file = args.file
    else:
        cards_file = SEEDS_DIR / TYPE_TO_FILE[args.card_type]

    if not cards_file.exists():
        print(f"[ERROR] Файл не найден: {cards_file}")
        sys.exit(1)

    load_cards(client, cards_file)

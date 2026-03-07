#!/usr/bin/env python3
"""
Seed script: загружает topics из topics.json в Supabase.

Использование:
    python database/seeds/load_topics.py

Требует переменных окружения:
    SUPABASE_URL           — URL проекта Supabase
    SUPABASE_SERVICE_ROLE_KEY — ключ с правами обхода RLS

Зависимости:
    pip install supabase python-dotenv
"""

from __future__ import annotations

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
TOPICS_FILE = SEEDS_DIR / "topics.json"
ENV_FILE = SEEDS_DIR.parent.parent / "backend" / ".env"


def load_env() -> None:
    """Load .env from backend directory if it exists."""
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
    else:
        load_dotenv()  # try CWD .env


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

def load_topics(client: Client) -> None:
    with TOPICS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    topics: list[dict] = data["topics"]
    print(f"[INFO] Загружено {len(topics)} тем из {TOPICS_FILE.name}")

    # Fetch existing topics to build code → id map
    existing_response = client.table("topics").select("id, code").execute()
    code_to_id: dict[str, str] = {
        row["code"]: row["id"] for row in (existing_response.data or [])
    }

    inserted = 0
    skipped = 0

    # Process level-by-level so parent_id resolution works
    for level in (0, 1, 2):
        level_topics = [t for t in topics if t["level"] == level]
        print(f"[INFO] Обрабатываем уровень {level}: {len(level_topics)} тем")

        for topic in level_topics:
            code = topic["code"]

            if code in code_to_id:
                print(f"  [SKIP] {code} — уже существует")
                skipped += 1
                continue

            # Resolve parent_id
            parent_id: str | None = None
            parent_code = topic.get("parent_code")
            if parent_code:
                parent_id = code_to_id.get(parent_code)
                if parent_id is None:
                    print(
                        f"  [WARN] {code}: родительская тема '{parent_code}' "
                        "не найдена — parent_id будет NULL"
                    )

            row = {
                "code": code,
                "title": topic["title"],
                "description": topic.get("description"),
                "difficulty": topic["difficulty"],
                "level": topic["level"],
                "parent_id": parent_id,
                "ege_task_numbers": topic["ege_task_numbers"],
            }

            result = client.table("topics").insert(row).execute()
            if result.data:
                new_id: str = result.data[0]["id"]
                code_to_id[code] = new_id
                print(f"  [OK]   {code} — вставлена (id={new_id[:8]}...)")
                inserted += 1
            else:
                print(f"  [ERROR] {code} — ошибка вставки: {result}")

    print(
        f"\n[DONE] Вставлено: {inserted}, пропущено (уже в БД): {skipped}, "
        f"всего в файле: {len(topics)}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    load_env()
    client = get_supabase_client()
    load_topics(client)

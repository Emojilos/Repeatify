#!/usr/bin/env python3
"""
Seed script: загружает topic_dependencies из topic_dependencies.json в Supabase.

Использование:
    python database/seeds/load_dependencies.py

Требует переменных окружения:
    SUPABASE_URL              — URL проекта Supabase
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
DEPS_FILE = SEEDS_DIR / "topic_dependencies.json"
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
# DAG cycle detection
# ---------------------------------------------------------------------------

def has_cycle(edges: list[tuple[str, str]]) -> bool:
    """Return True if the directed graph defined by edges contains a cycle."""
    graph: dict[str, list[str]] = {}
    for src, dst in edges:
        graph.setdefault(src, []).append(dst)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            c = color.get(neighbor, WHITE)
            if c == GRAY:
                return True
            if c == WHITE and dfs(neighbor):
                return True
        color[node] = BLACK
        return False

    all_nodes = set(graph.keys()) | {dst for _, dst in edges}
    for node in all_nodes:
        if color.get(node, WHITE) == WHITE:
            if dfs(node):
                return True
    return False


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_dependencies(client: Client) -> None:
    with DEPS_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    deps: list[dict] = data["dependencies"]
    print(f"[INFO] Загружено {len(deps)} зависимостей из {DEPS_FILE.name}")

    # --- DAG validation ---
    edges = [(d["prerequisite_topic_code"], d["dependent_topic_code"]) for d in deps]
    if has_cycle(edges):
        print("[ERROR] Обнаружен цикл в графе зависимостей! Загрузка прервана.")
        sys.exit(1)
    print("[INFO] Граф зависимостей проверен — циклов нет (DAG валиден)")

    # --- Fetch all topics: build code → id map ---
    topic_response = client.table("topics").select("id, code").execute()
    if not topic_response.data:
        print("[ERROR] Таблица topics пуста или недоступна. Сначала запустите load_topics.py")
        sys.exit(1)

    code_to_id: dict[str, str] = {row["code"]: row["id"] for row in topic_response.data}
    print(f"[INFO] Получено {len(code_to_id)} тем из БД")

    # --- Fetch existing dependencies to avoid duplicates ---
    existing_response = (
        client.table("topic_dependencies")
        .select("prerequisite_topic_id, dependent_topic_id")
        .execute()
    )
    existing_pairs: set[tuple[str, str]] = {
        (row["prerequisite_topic_id"], row["dependent_topic_id"])
        for row in (existing_response.data or [])
    }

    inserted = 0
    skipped = 0
    errors = 0

    for dep in deps:
        prereq_code = dep["prerequisite_topic_code"]
        dep_code = dep["dependent_topic_code"]

        prereq_id = code_to_id.get(prereq_code)
        dep_id = code_to_id.get(dep_code)

        if prereq_id is None:
            print(f"  [ERROR] Тема-предпосылка '{prereq_code}' не найдена в БД — пропуск")
            errors += 1
            continue

        if dep_id is None:
            print(f"  [ERROR] Зависимая тема '{dep_code}' не найдена в БД — пропуск")
            errors += 1
            continue

        if (prereq_id, dep_id) in existing_pairs:
            print(f"  [SKIP] {prereq_code} → {dep_code} — уже существует")
            skipped += 1
            continue

        row = {
            "prerequisite_topic_id": prereq_id,
            "dependent_topic_id": dep_id,
            "weight": dep["weight"],
            "relationship_type": dep["relationship_type"],
        }

        result = client.table("topic_dependencies").insert(row).execute()
        if result.data:
            existing_pairs.add((prereq_id, dep_id))
            print(f"  [OK]   {prereq_code} → {dep_code} (weight={dep['weight']})")
            inserted += 1
        else:
            print(f"  [ERROR] {prereq_code} → {dep_code}: ошибка вставки: {result}")
            errors += 1

    print(
        f"\n[DONE] Вставлено: {inserted}, пропущено (уже в БД): {skipped}, "
        f"ошибок: {errors}, всего в файле: {len(deps)}"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    load_env()
    client = get_supabase_client()
    load_dependencies(client)

"""Normalizer: clean, deduplicate, and upload parsed problems to the database.

Accepts JSON files produced by shkolkovo_parser.py and math100_parser.py.
Performs:
  1. HTML artifact cleanup (stray tags, entities, nbsp)
  2. LaTeX normalization (consistent delimiters, whitespace)
  3. Deduplication by content_hash (checks existing DB records)
  4. Prototype linking by task_number heuristics
  5. Bulk INSERT into the problems table via Supabase

Usage:
  python tools/parsers/normalizer.py --input problems_shkolkovo.json
  python tools/parsers/normalizer.py --input a.json b.json --dry-run
  python tools/parsers/normalizer.py --input problems.json --recompute-hashes
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML / LaTeX cleaning
# ---------------------------------------------------------------------------

# Common HTML entities that slip through parsers
_HTML_ENTITIES = {
    "&nbsp;": " ",
    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&quot;": '"',
    "&#39;": "'",
    "&mdash;": "—",
    "&ndash;": "–",
    "&laquo;": "«",
    "&raquo;": "»",
}

# Regex to match stray HTML tags (not LaTeX)
_HTML_TAG_RE = re.compile(
    r"<(?!/)?\s*(?:br|span|div|p|em|strong|b|i|u|font|a|img)[^>]*>",
    re.IGNORECASE,
)
_HTML_CLOSE_TAG_RE = re.compile(
    r"</\s*(?:br|span|div|p|em|strong|b|i|u|font|a)>",
    re.IGNORECASE,
)


def clean_html_artifacts(text: str) -> str:
    """Remove residual HTML tags and decode entities."""
    if not text:
        return text

    # Decode HTML entities
    for entity, replacement in _HTML_ENTITIES.items():
        text = text.replace(entity, replacement)

    # Remove stray HTML tags (preserve LaTeX \langle, \left< etc.)
    text = _HTML_TAG_RE.sub("", text)
    text = _HTML_CLOSE_TAG_RE.sub("", text)

    # Remove any remaining &#NNN; numeric entities
    text = re.sub(r"&#\d+;", "", text)

    return text.strip()


def normalize_latex(text: str) -> str:
    r"""Normalize LaTeX delimiters and whitespace.

    Converts:
      \( ... \)  →  $ ... $
      \[ ... \]  →  $$ ... $$
    Collapses excessive whitespace inside math environments.
    """
    if not text:
        return text

    # Convert \( ... \) to $ ... $ (inline math)
    text = re.sub(r"\\\(\s*", "$", text)
    text = re.sub(r"\s*\\\)", "$", text)

    # Convert \[ ... \] to $$ ... $$ (display math)
    text = re.sub(r"\\\[\s*", "$$", text)
    text = re.sub(r"\s*\\\]", "$$", text)

    # Collapse multiple spaces (but not newlines) inside and outside math
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse multiple blank lines into one
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def clean_problem_text(text: str) -> str:
    """Full cleaning pipeline for problem text."""
    text = clean_html_artifacts(text)
    text = normalize_latex(text)
    return text


# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------

def compute_content_hash(text: str) -> str:
    """Compute SHA-256 hash of normalized text for deduplication.

    Same algorithm as ParsedProblem.compute_hash() in parsers.
    """
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NormalizedProblem:
    """A problem ready for database insertion."""

    task_number: int
    problem_text: str
    correct_answer: str | None = None
    problem_images: list[str] = field(default_factory=list)
    source: str = ""
    source_url: str = ""
    content_hash: str = ""
    difficulty: str = "medium"


@dataclass
class NormalizerStats:
    """Statistics from a normalization run."""

    total_input: int = 0
    cleaned: int = 0
    duplicates_in_file: int = 0
    duplicates_in_db: int = 0
    no_topic: int = 0
    inserted: int = 0
    failed: int = 0

    def summary(self) -> str:
        dupes = self.duplicates_in_file + self.duplicates_in_db
        return (
            f"Added: {self.inserted}, "
            f"Skipped (duplicates): {dupes}, "
            f"Skipped (no topic): {self.no_topic}, "
            f"Failed: {self.failed}, "
            f"Total input: {self.total_input}"
        )


# ---------------------------------------------------------------------------
# Loading and normalizing
# ---------------------------------------------------------------------------

def load_problems_from_json(paths: list[str | Path]) -> list[dict]:
    """Load and merge problems from one or more JSON files."""
    all_problems: list[dict] = []
    for path in paths:
        path = Path(path)
        if not path.exists():
            log.warning("File not found: %s", path)
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            all_problems.extend(data)
        elif isinstance(data, dict):
            all_problems.append(data)
        else:
            log.warning("Unexpected JSON structure in %s", path)
        count = len(data) if isinstance(data, list) else 1
        log.info("Loaded %d problems from %s", count, path)
    return all_problems


def normalize_problems(
    raw_problems: list[dict],
    recompute_hashes: bool = False,
) -> tuple[list[NormalizedProblem], NormalizerStats]:
    """Clean and deduplicate a list of raw problem dicts.

    Returns normalized problems and stats. Deduplication within the batch
    is done here; DB deduplication happens at upload time.
    """
    stats = NormalizerStats(total_input=len(raw_problems))
    seen_hashes: set[str] = set()
    results: list[NormalizedProblem] = []

    for raw in raw_problems:
        task_number = raw.get("task_number")
        problem_text = raw.get("problem_text", "")

        if not problem_text or not task_number:
            stats.failed += 1
            continue

        # Clean
        cleaned_text = clean_problem_text(problem_text)
        stats.cleaned += 1

        # Hash
        if recompute_hashes or not raw.get("content_hash"):
            content_hash = compute_content_hash(cleaned_text)
        else:
            content_hash = raw["content_hash"]

        # In-batch dedup
        if content_hash in seen_hashes:
            stats.duplicates_in_file += 1
            continue
        seen_hashes.add(content_hash)

        # Clean answer
        answer = raw.get("correct_answer")
        if answer is not None:
            answer = str(answer).strip()

        # Clean images
        images = raw.get("problem_images", [])
        if not isinstance(images, list):
            images = []

        results.append(NormalizedProblem(
            task_number=int(task_number),
            problem_text=cleaned_text,
            correct_answer=answer if answer else None,
            problem_images=images,
            source=raw.get("source", ""),
            source_url=raw.get("source_url", ""),
            content_hash=content_hash,
            difficulty=raw.get("difficulty", "medium"),
        ))

    return results, stats


# ---------------------------------------------------------------------------
# Prototype linking
# ---------------------------------------------------------------------------

def link_prototypes(
    problems: list[NormalizedProblem],
    prototype_map: dict[int, list[dict]],
) -> list[NormalizedProblem]:
    """Assign prototype_id to problems based on task_number.

    If a task_number has exactly one prototype, assign it directly.
    If multiple prototypes exist, assign the first one (by order_index).
    This is a simple heuristic; manual curation may refine it later.
    """
    for problem in problems:
        prototypes = prototype_map.get(problem.task_number, [])
        if len(prototypes) == 1:
            problem._prototype_id = prototypes[0]["id"]  # type: ignore[attr-defined]
        elif len(prototypes) > 1:
            # Pick the first by order_index (already sorted from DB query)
            problem._prototype_id = prototypes[0]["id"]  # type: ignore[attr-defined]
        else:
            problem._prototype_id = None  # type: ignore[attr-defined]
    return problems


# ---------------------------------------------------------------------------
# Upload to Supabase
# ---------------------------------------------------------------------------

def fetch_existing_hashes(client: object) -> set[str]:
    """Fetch all content_hash values already in the problems table."""
    resp = (
        client.table("problems")  # type: ignore[union-attr]
        .select("content_hash")
        .not_.is_("content_hash", "null")
        .execute()
    )
    return {row["content_hash"] for row in (resp.data or []) if row.get("content_hash")}


def fetch_topic_map(client: object) -> dict[int, str]:
    """Fetch task_number -> topic_id mapping from topics table."""
    resp = client.table("topics").select("id,task_number").execute()  # type: ignore[union-attr]
    result: dict[int, str] = {}
    for row in resp.data or []:
        result[row["task_number"]] = row["id"]
    return result


def fetch_prototype_map(client: object) -> dict[int, list[dict]]:
    """Fetch task_number -> list of prototypes mapping."""
    resp = (
        client.table("prototypes")  # type: ignore[union-attr]
        .select("id,task_number,prototype_code,order_index")
        .order("order_index")
        .execute()
    )
    result: dict[int, list[dict]] = {}
    for row in resp.data or []:
        tn = row["task_number"]
        if tn not in result:
            result[tn] = []
        result[tn].append(row)
    return result


def upload_problems(
    problems: list[NormalizedProblem],
    stats: NormalizerStats,
    dry_run: bool = False,
) -> NormalizerStats:
    """Upload normalized problems to Supabase.

    Performs DB-level deduplication by content_hash, links to topic_id
    and prototype_id, and inserts via Supabase client.
    """
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(_project_root / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        log.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for upload")
        return stats

    client = create_client(url, key)

    # Fetch DB state
    existing_hashes = fetch_existing_hashes(client)
    topic_map = fetch_topic_map(client)
    prototype_map = fetch_prototype_map(client)

    # Link prototypes
    problems = link_prototypes(problems, prototype_map)

    for problem in problems:
        # DB dedup
        if problem.content_hash in existing_hashes:
            stats.duplicates_in_db += 1
            continue

        # Topic lookup
        topic_id = topic_map.get(problem.task_number)
        if not topic_id:
            log.warning("No topic for task_number %d, skipping", problem.task_number)
            stats.no_topic += 1
            continue

        prototype_id = getattr(problem, "_prototype_id", None)

        row = {
            "topic_id": topic_id,
            "task_number": problem.task_number,
            "difficulty": problem.difficulty,
            "problem_text": problem.problem_text,
            "correct_answer": problem.correct_answer or "",
            "problem_images": problem.problem_images,
            "source": problem.source,
            "source_url": problem.source_url,
            "content_hash": problem.content_hash,
        }
        if prototype_id:
            row["prototype_id"] = prototype_id

        if dry_run:
            log.info(
                "[DRY RUN] Would insert: task=%d hash=%s...",
                problem.task_number,
                problem.content_hash[:12],
            )
            stats.inserted += 1
            continue

        try:
            client.table("problems").insert(row).execute()
            stats.inserted += 1
            existing_hashes.add(problem.content_hash)
        except Exception as e:
            log.warning(
                "Failed to insert (hash=%s): %s",
                problem.content_hash[:12],
                e,
            )
            stats.failed += 1

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Normalize, deduplicate, and upload "
        "parsed EGE problems to Supabase.",
    )
    parser.add_argument(
        "--input", "-i",
        nargs="+",
        required=True,
        help="One or more JSON files from parsers",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be inserted without actually writing to DB",
    )
    parser.add_argument(
        "--recompute-hashes",
        action="store_true",
        help="Recompute content_hash from cleaned text instead of using parser's hash",
    )

    args = parser.parse_args(argv)

    # Load
    raw_problems = load_problems_from_json(args.input)
    if not raw_problems:
        log.error("No problems loaded from input files")
        sys.exit(1)

    # Normalize
    problems, stats = normalize_problems(
        raw_problems, recompute_hashes=args.recompute_hashes,
    )
    log.info(
        "Normalized %d problems (from %d raw)",
        len(problems), stats.total_input,
    )

    # Upload
    stats = upload_problems(problems, stats, dry_run=args.dry_run)

    # Report
    log.info(stats.summary())


if __name__ == "__main__":
    main()

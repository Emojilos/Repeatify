"""Parser for math-ege.sdamgia.ru — «Решу ЕГЭ» math problem bank.

Standalone script that scrapes EGE math problems from sdamgia.ru by task number.
Extracts: problem text (with LaTeX), images, correct answer, solution.
Generates content_hash (SHA-256) for deduplication.

Uses Tavily extract API for JS-rendered content since sdamgia loads
content dynamically.

Usage:
  python tools/parsers/sdamgia_parser.py --task-number 1
  python tools/parsers/sdamgia_parser.py --task-number 6 --max-problems 20
  python tools/parsers/sdamgia_parser.py --task-number 1 --output problems_1.json
  python tools/parsers/sdamgia_parser.py --task-number 1 --upload --upload-images
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from image_downloader import process_images

_project_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://math-ege.sdamgia.ru"
# Theme page lists problems for a given EGE task number
THEME_URL = BASE_URL + "/test?theme={theme_id}"
# Individual problem page
PROBLEM_URL = BASE_URL + "/problem?id={problem_id}"

# Polite delay between requests (seconds)
REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# Mapping from EGE task number (1-19) to sdamgia internal theme IDs.
# Each task may have multiple subtopics; we list the main ones.
# "Тип N" = current format, "Тип ДN" = deprecated format.
# Gathered from https://math-ege.sdamgia.ru/prob-catalog
TASK_TO_THEME_IDS: dict[int, list[int]] = {
    1: [55, 56, 57, 58, 59],                # Планиметрия (Тип 1)
    2: [10],                                  # Векторы (Тип 2)
    3: [11, 12, 13, 14],                     # Стереометрия (Тип 3)
    4: [61, 62, 63],                          # Вероятности (Тип 4)
    5: [64, 65],                              # Вероятности (Тип 5)
    6: [68, 69, 70],                          # Уравнения (Тип 6)
    7: [60],                                  # Вычисления (Тип 7)
    8: [7, 8, 9],                             # Производная (Тип 8)
    9: [90],                                  # Задачи с прикладным содержанием (Тип 9)
    10: [84, 85, 86, 87, 88, 89],            # Текстовые задачи (Тип 10)
    11: [122, 125, 191, 267, 272, 294, 296], # Графики функций (Тип 11)
    12: [78, 80, 81, 82, 83],                # Наибольшее/наименьшее значение (Тип 12)
    13: [201, 202, 275, 290, 291],           # Уравнения (Тип 13)
    14: [206, 257, 280, 281, 282, 283],      # Стереометрия (Тип 14)
    15: [237, 238, 239, 242, 243, 244, 245], # Неравенства (Тип 15)
    16: [221, 247, 292, 293],                 # Экономическая задача (Тип 16)
    17: [276, 277, 278, 279],                 # Планиметрия (Тип 17)
    18: [207, 208, 235, 266, 268, 269, 270], # Параметр (Тип 18)
    19: [209, 210, 217],                      # Числа и их свойства (Тип 19)
}


@dataclass
class ParsedProblem:
    """A single parsed problem."""

    task_number: int
    problem_text: str
    correct_answer: str | None = None
    solution_text: str | None = None
    problem_images: list[str] = field(default_factory=list)
    source: str = "sdamgia"
    source_url: str = ""
    source_id: str = ""
    content_hash: str = ""
    difficulty: str = "medium"

    def compute_hash(self) -> None:
        """Compute SHA-256 hash of problem text + images for deduplication.

        Includes image URLs in the hash because many sdamgia problems
        have identical text (e.g. "Найдите значение выражения") but
        different formula images.
        """
        normalized = re.sub(r"\s+", " ", self.problem_text).strip()
        # Include image URLs to differentiate problems with same text
        images_str = "|".join(sorted(self.problem_images))
        # Include source_id as ultimate differentiator
        combined = f"{normalized}|{images_str}|{self.source_id}"
        self.content_hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()


def fetch_page(url: str, session: requests.Session) -> BeautifulSoup | None:
    """Fetch a URL and return parsed BeautifulSoup, or None on error."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return None


def clean_sdamgia_text(text: str) -> str:
    """Clean sdamgia-specific text artifacts.

    sdamgia inserts soft hyphens (­) and uses specific formatting
    that needs cleanup.
    """
    # Remove soft hyphens
    text = text.replace("\u00ad", "")
    text = text.replace("­", "")
    # Clean up whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_task_type_from_page(soup: BeautifulSoup) -> int | None:
    """Extract actual EGE task type ('Тип N') from a problem page.

    SDAMGIA marks each problem with 'Тип N' where N is the EGE 2025 task number.
    Returns None if not found.
    """
    text = soup.get_text()
    m = re.search(r"Тип\s+(\d{1,2})", text)
    if m:
        return int(m.group(1))
    return None


def extract_problem_ids_from_theme(
    soup: BeautifulSoup, task_number: int
) -> list[str]:
    """Extract problem IDs from a theme/catalog page.

    sdamgia lists problems with IDs in format "Тип {N}№{ID}" or
    links to /problem?id={ID}.
    """
    problem_ids: list[str] = []

    # Look for problem ID patterns in the page text
    # Format: "№{number}" in problem headers
    text = soup.get_text()
    # Match patterns like "№323512" or "№ 323512"
    for match in re.finditer(r"№\s*(\d{4,})", text):
        pid = match.group(1)
        if pid not in problem_ids:
            problem_ids.append(pid)

    # Also look for links containing problem IDs
    for a_tag in soup.find_all("a", href=True):
        href = str(a_tag["href"])
        m = re.search(r"problem\?id=(\d+)", href)
        if m:
            pid = m.group(1)
            if pid not in problem_ids:
                problem_ids.append(pid)

    return problem_ids


def extract_images_from_content(
    soup: BeautifulSoup | Tag, base_url: str = BASE_URL
) -> list[str]:
    """Extract relevant image URLs from problem content.

    Includes both regular images (/get_file?id=) and formula SVGs.
    Skips icons, logos, and UI elements.
    """
    images: list[str] = []
    skip_patterns = [
        "/img/headers/",
        "/img/briefcase",
        "/img/exclamation",
        "/img/light",
        "yandex",
        "mail.ru",
        "counter",
        "pixel",
        "logo",
        "banner",
    ]

    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue

        # Skip UI/tracking images
        if any(pat in src.lower() for pat in skip_patterns):
            continue

        # Skip tiny icons
        width = img.get("width", "")
        height = img.get("height", "")
        try:
            if width and int(width) < 15:
                continue
            if height and int(height) < 15:
                continue
        except ValueError:
            pass

        # Make absolute URL
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = base_url + src
        elif not src.startswith("http"):
            src = base_url + "/" + src

        if src not in images:
            images.append(src)

    return images


def parse_problem_from_theme_page(
    raw_content: str, problem_id: str, task_number: int
) -> ParsedProblem | None:
    """Parse a single problem from extracted page content.

    The raw_content is markdown-formatted text from Tavily extract.
    """
    if not raw_content:
        return None

    # Find the problem text — it's between the problem header and "Решение"/"Ответ"
    # Clean the text first
    text = clean_sdamgia_text(raw_content)

    if len(text) < 20:
        return None

    # Try to extract answer
    answer = None
    answer_match = re.search(r"Ответ:\s*(.+?)(?:\n|$)", text)
    if answer_match:
        answer = answer_match.group(1).strip().rstrip(".")

    # Try to extract solution
    solution = None
    solution_match = re.search(
        r"Ре­?ше­?ние[.:]\s*(.*?)(?:Ответ:|Спрятать|Критерии|$)",
        text,
        re.DOTALL,
    )
    if solution_match:
        solution = solution_match.group(1).strip()
        if len(solution) < 10:
            solution = None

    problem = ParsedProblem(
        task_number=task_number,
        problem_text=text,
        correct_answer=answer,
        solution_text=solution,
        source_url=PROBLEM_URL.format(problem_id=problem_id),
        source_id=problem_id,
    )
    problem.compute_hash()
    return problem


def scrape_with_requests(
    task_number: int,
    max_problems: int = 30,
) -> list[ParsedProblem]:
    """Scrape problems using direct HTTP requests.

    This works for sdamgia pages that render server-side.
    """
    theme_ids = TASK_TO_THEME_IDS.get(task_number, [])
    if not theme_ids:
        log.error("No theme IDs mapped for task %d", task_number)
        return []

    session = requests.Session()
    problem_ids: list[str] = []

    # Collect problem IDs from all theme pages for this task
    for theme_id in theme_ids:
        theme_url = THEME_URL.format(theme_id=theme_id)
        log.info("Fetching theme page: %s", theme_url)

        soup = fetch_page(theme_url, session)
        if soup is None:
            continue

        ids = extract_problem_ids_from_theme(soup, task_number)
        for pid in ids:
            if pid not in problem_ids:
                problem_ids.append(pid)
        log.info("Found %d problem IDs from theme %d", len(ids), theme_id)
        time.sleep(REQUEST_DELAY)

    log.info("Total %d unique problem IDs for task %d", len(problem_ids), task_number)

    if not problem_ids:
        log.info("No problem IDs found")

    problems: list[ParsedProblem] = []
    seen_hashes: set[str] = set()

    # Parse individual problem pages
    for pid in problem_ids[:max_problems]:
        prob_url = PROBLEM_URL.format(problem_id=pid)
        log.info("Fetching problem %s", pid)
        time.sleep(REQUEST_DELAY)

        prob_soup = fetch_page(prob_url, session)
        if prob_soup is None:
            continue

        # Find problem body — sdamgia uses class "pbody" or similar
        pbody = prob_soup.select_one(".pbody")
        if pbody is None:
            # Try alternative selectors
            pbody = prob_soup.select_one(".condition") or prob_soup.select_one(
                ".maincontent"
            )

        if pbody is None:
            # Fallback: get main content area
            pbody = prob_soup.select_one(".sgia-main-content")

        if pbody is None:
            log.warning("Could not find problem body for %s", pid)
            continue

        # Extract images from problem body first (needed for validity check)
        image_urls = extract_images_from_content(pbody)

        problem_text = clean_sdamgia_text(pbody.get_text(separator=" ", strip=True))
        # Accept short text if there are images (formula SVGs count as content)
        if len(problem_text) < 10 and not image_urls:
            log.warning("Problem text too short and no images for %s", pid)
            continue

        # Extract answer
        answer = None
        answer_el = prob_soup.select_one(".answer")
        if answer_el:
            answer = clean_sdamgia_text(answer_el.get_text(strip=True))
            answer = re.sub(r"^Ответ:?\s*", "", answer).strip().rstrip(".")

        # Also try finding answer in text
        if not answer:
            answer_match = re.search(r"Ответ:\s*(.+?)(?:\n|$)", problem_text)
            if answer_match:
                answer = answer_match.group(1).strip().rstrip(".")

        # Extract actual task type from problem page (EGE 2025 numbering)
        actual_type = extract_task_type_from_page(prob_soup)
        effective_task = actual_type if actual_type else task_number
        if actual_type and actual_type != task_number:
            log.info(
                "Problem %s: page says Тип %d (requested task %d)",
                pid, actual_type, task_number,
            )

        problem = ParsedProblem(
            task_number=effective_task,
            problem_text=problem_text,
            correct_answer=answer,
            problem_images=image_urls,  # raw URLs for hashing
            source_url=prob_url,
            source_id=pid,
        )
        problem.compute_hash()

        if problem.content_hash in seen_hashes:
            continue
        seen_hashes.add(problem.content_hash)

        # Download images locally (replace URLs with local paths)
        if image_urls:
            problem.problem_images = process_images(
                image_urls=image_urls,
                source="sdamgia",
                task_number=effective_task,
                content_hash=problem.content_hash,
                session=session,
            )

        problems.append(problem)
        log.info(
            "Parsed problem %d (id=%s, type=%d, hash=%s...)",
            len(problems),
            pid,
            effective_task,
            problem.content_hash[:12],
        )

    return problems


def scrape_with_tavily(
    task_number: int,
    max_problems: int = 30,
) -> list[ParsedProblem]:
    """Scrape problems using Tavily extract API for JS-rendered content.

    Falls back to this method if direct requests don't work well.
    Requires TAVILY_API_KEY environment variable.
    """
    from dotenv import load_dotenv

    load_dotenv(_project_root / ".env")

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        log.error("TAVILY_API_KEY is required for Tavily extraction")
        return []

    theme_ids = TASK_TO_THEME_IDS.get(task_number, [])
    if not theme_ids:
        log.error("No theme IDs mapped for task %d", task_number)
        return []

    theme_urls = [
        THEME_URL.format(theme_id=tid) for tid in theme_ids
    ]
    log.info("Extracting %d theme pages via Tavily", len(theme_urls))

    # Extract theme pages to get problem IDs
    try:
        resp = requests.post(
            "https://api.tavily.com/extract",
            json={
                "urls": theme_urls,
                "api_key": api_key,
                "extract_depth": "advanced",
                "include_images": True,
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        log.error("Tavily extract failed: %s", e)
        return []

    results = data.get("results", [])
    if not results:
        log.warning("No results from Tavily extract")
        return []

    # Collect problem IDs from all theme pages
    problem_ids: list[str] = []
    for result in results:
        raw_content = result.get("raw_content", "")
        for match in re.finditer(r"№\s*(\d{4,})", raw_content):
            pid = match.group(1)
            if pid not in problem_ids:
                problem_ids.append(pid)

    log.info("Found %d problem IDs from Tavily content", len(problem_ids))

    # Split content by problem markers and parse each
    problems: list[ParsedProblem] = []
    seen_hashes: set[str] = set()
    session = requests.Session()

    # Parse problems from individual pages via Tavily
    batch_size = 5
    for i in range(0, min(len(problem_ids), max_problems), batch_size):
        batch_ids = problem_ids[i : i + batch_size]
        batch_urls = [
            PROBLEM_URL.format(problem_id=pid) for pid in batch_ids
        ]

        log.info("Extracting batch of %d problems via Tavily", len(batch_urls))

        try:
            resp = requests.post(
                "https://api.tavily.com/extract",
                json={
                    "urls": batch_urls,
                    "api_key": api_key,
                    "extract_depth": "advanced",
                    "include_images": True,
                },
                timeout=120,
            )
            resp.raise_for_status()
            batch_data = resp.json()
        except Exception as e:
            log.warning("Tavily batch extract failed: %s", e)
            continue

        for result in batch_data.get("results", []):
            url = result.get("url", "")
            content = result.get("raw_content", "")
            images = result.get("images", [])

            # Extract problem ID from URL
            id_match = re.search(r"id=(\d+)", url)
            pid = id_match.group(1) if id_match else "unknown"

            if not content or len(content) < 50:
                continue

            # Clean the content
            content = clean_sdamgia_text(content)

            # Extract just the problem text (before solution/navigation)
            # Look for the problem statement
            problem_text = content

            # Try to extract answer
            answer = None
            answer_match = re.search(r"Ответ:\s*(.+?)(?:\n|$)", content)
            if answer_match:
                answer = answer_match.group(1).strip().rstrip(".")

            # Filter images — only keep problem-relevant ones
            problem_images = [
                img
                for img in images
                if (
                    "/get_file?" in img
                    or "/formula/svg/" in img
                )
                and "logo" not in img.lower()
                and "header" not in img.lower()
            ]

            # Extract actual task type from content (EGE 2025 numbering)
            type_match = re.search(r"Тип\s+(\d{1,2})", content)
            effective_task = int(type_match.group(1)) if type_match else task_number
            if type_match and effective_task != task_number:
                log.info(
                    "Problem %s: content says Тип %d (requested task %d)",
                    pid, effective_task, task_number,
                )

            problem = ParsedProblem(
                task_number=effective_task,
                problem_text=problem_text,
                correct_answer=answer,
                problem_images=[],
                source_url=url,
                source_id=pid,
            )
            problem.compute_hash()

            if problem.content_hash in seen_hashes:
                continue
            seen_hashes.add(problem.content_hash)

            # Download images
            if problem_images:
                problem.problem_images = process_images(
                    image_urls=problem_images,
                    source="sdamgia",
                    task_number=effective_task,
                    content_hash=problem.content_hash,
                    session=session,
                )

            problems.append(problem)
            log.info(
                "Parsed problem %d (id=%s, hash=%s...)",
                len(problems),
                pid,
                problem.content_hash[:12],
            )

        time.sleep(REQUEST_DELAY)

    return problems


def scrape_task(
    task_number: int,
    max_problems: int = 30,
    use_tavily: bool = False,
) -> list[ParsedProblem]:
    """Scrape problems for a given task number from sdamgia.ru.

    Args:
        task_number: EGE task number (1-19).
        max_problems: Maximum problems to collect.
        use_tavily: Use Tavily API for JS-rendered content.

    Returns:
        List of parsed problems.
    """
    if not 1 <= task_number <= 19:
        log.error("Task number must be 1-19, got %d", task_number)
        return []

    log.info("Starting scrape for task %d from sdamgia.ru", task_number)

    if use_tavily:
        problems = scrape_with_tavily(task_number, max_problems)
    else:
        problems = scrape_with_requests(task_number, max_problems)

    log.info(
        "Scrape complete for task %d: %d problems collected",
        task_number,
        len(problems),
    )
    return problems


def upload_to_supabase(
    problems: list[ParsedProblem], upload_images: bool = False
) -> int:
    """Upload parsed problems to Supabase.

    Requires SUPABASE_URL and SUPABASE_SERVICE_KEY in .env.
    Returns number of inserted problems.
    """
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(_project_root / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        log.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set for upload")
        return 0

    client = create_client(url, key)

    # Fetch existing hashes for deduplication
    existing = (
        client.table("problems")
        .select("content_hash")
        .eq("source", "sdamgia")
        .execute()
    )
    existing_hashes = {
        row["content_hash"]
        for row in (existing.data or [])
        if row.get("content_hash")
    }

    # Find the topic_id for each task_number
    topics_resp = client.table("topics").select("id,task_number").execute()
    topic_map: dict[int, str] = {}
    for row in topics_resp.data or []:
        topic_map[row["task_number"]] = row["id"]

    inserted = 0
    skipped = 0

    for problem in problems:
        if problem.content_hash in existing_hashes:
            skipped += 1
            continue

        topic_id = topic_map.get(problem.task_number)
        if not topic_id:
            log.warning(
                "No topic found for task_number %d, skipping",
                problem.task_number,
            )
            skipped += 1
            continue

        # Upload images to Supabase Storage if requested
        images = problem.problem_images
        if upload_images and images:
            from image_downloader import upload_images_to_storage

            images = upload_images_to_storage(
                images, "sdamgia", problem.task_number
            )

        row = {
            "topic_id": topic_id,
            "task_number": problem.task_number,
            "difficulty": problem.difficulty,
            "problem_text": problem.problem_text,
            "correct_answer": problem.correct_answer or "",
            "problem_images": images,
            "source": problem.source,
            "source_url": problem.source_url,
            "content_hash": problem.content_hash,
        }

        try:
            client.table("problems").insert(row).execute()
            inserted += 1
        except Exception as e:
            log.warning("Failed to insert problem: %s", e)
            skipped += 1

    log.info(
        "Upload complete. Added: %d, Skipped (duplicates): %d", inserted, skipped
    )
    return inserted


def save_to_json(problems: list[ParsedProblem], output_path: str) -> None:
    """Save parsed problems to a JSON file."""
    data = [asdict(p) for p in problems]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Saved %d problems to %s", len(problems), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse EGE math problems from math-ege.sdamgia.ru",
    )
    parser.add_argument(
        "--task-number",
        type=int,
        required=True,
        help="EGE task number (1-19)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output JSON file path (default: sdamgia_task_{N}.json)",
    )
    parser.add_argument(
        "--max-problems",
        type=int,
        default=30,
        help="Maximum problems to collect (default: 30)",
    )
    parser.add_argument(
        "--use-tavily",
        action="store_true",
        help="Use Tavily API for JS-rendered content extraction",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload parsed problems to Supabase",
    )
    parser.add_argument(
        "--upload-images",
        action="store_true",
        help="Upload downloaded images to Supabase Storage (requires --upload)",
    )

    args = parser.parse_args()

    if not 1 <= args.task_number <= 19:
        log.error("Task number must be between 1 and 19")
        sys.exit(1)

    problems = scrape_task(
        task_number=args.task_number,
        max_problems=args.max_problems,
        use_tavily=args.use_tavily,
    )

    if not problems:
        log.warning("No problems parsed. Check the site structure or selectors.")
        sys.exit(0)

    # Save to JSON
    output_path = args.output or f"sdamgia_task_{args.task_number}.json"
    save_to_json(problems, output_path)

    # Optionally upload to Supabase
    if args.upload:
        upload_to_supabase(problems, upload_images=args.upload_images)


if __name__ == "__main__":
    main()

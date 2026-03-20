"""Parser for 3.shkolkovo.online — EGE math problem bank.

Standalone script that scrapes problems from Shkolkovo's catalog by task number.
Extracts: problem text (with LaTeX), images, correct answer, task number.
Generates content_hash (SHA-256) for deduplication.

Usage:
  python tools/parsers/shkolkovo_parser.py --task-number 6
  python tools/parsers/shkolkovo_parser.py --task-number 7 --output problems_7.json
  python tools/parsers/shkolkovo_parser.py --task-number 6 --max-pages 3
  python tools/parsers/shkolkovo_parser.py --task-number 6 --upload
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

_project_root = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

BASE_URL = "https://3.shkolkovo.online"
# Shkolkovo catalog URL pattern: /catalog/mathematics/zadanie-{N}-ege/
CATALOG_URL = BASE_URL + "/catalog/mathematics/zadanie-{task_number}-ege/"

# Polite delay between requests (seconds)
REQUEST_DELAY = 1.5
REQUEST_TIMEOUT = 15

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


@dataclass
class ParsedProblem:
    """A single parsed problem."""

    task_number: int
    problem_text: str
    correct_answer: str | None = None
    problem_images: list[str] = field(default_factory=list)
    source: str = "shkolkovo"
    source_url: str = ""
    content_hash: str = ""
    difficulty: str = "medium"

    def compute_hash(self) -> None:
        """Compute SHA-256 hash of problem text for deduplication."""
        normalized = re.sub(r"\s+", " ", self.problem_text).strip()
        self.content_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def fetch_page(url: str, session: requests.Session) -> BeautifulSoup | None:
    """Fetch a URL and return parsed BeautifulSoup, or None on error."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception as e:
        log.warning("Failed to fetch %s: %s", url, e)
        return None


def extract_text_with_latex(element: Tag) -> str:
    """Extract text from an element, preserving LaTeX markup.

    Shkolkovo uses MathJax/KaTeX with inline \\( ... \\) and display
    $$ ... $$ or \\[ ... \\] delimiters.  We normalize everything to
    standard $ / $$ delimiters for storage.
    """
    if element is None:
        return ""

    html = str(element)

    # Convert MathJax delimiters to standard LaTeX
    html = html.replace("\\(", "$").replace("\\)", "$")
    html = html.replace("\\[", "$$").replace("\\]", "$$")

    # Parse again to extract text with LaTeX preserved
    soup = BeautifulSoup(html, "lxml")

    # Remove script/style tags
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Get text, preserving LaTeX
    text = soup.get_text(separator=" ", strip=True)

    # Clean up whitespace but keep LaTeX intact
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_images(element: Tag, base_url: str = BASE_URL) -> list[str]:
    """Extract image URLs from a problem element."""
    images: list[str] = []
    if element is None:
        return images

    for img in element.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        # Skip tiny icons, tracking pixels
        width = img.get("width", "")
        height = img.get("height", "")
        if width and int(width) < 20:
            continue
        if height and int(height) < 20:
            continue
        # Make absolute URL
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = base_url + src
        elif not src.startswith("http"):
            src = base_url + "/" + src
        images.append(src)

    return images


def extract_answer(element: Tag) -> str | None:
    """Extract the correct answer from a problem element.

    Shkolkovo typically has the answer in a spoiler/collapse element or
    a dedicated answer block.
    """
    if element is None:
        return None

    # Look for answer containers by common class/id patterns
    answer_selectors = [
        ".answer",
        ".task-answer",
        ".correct-answer",
        "[data-answer]",
        ".spoiler-body",
        ".solution-answer",
        ".otvet",
    ]

    for selector in answer_selectors:
        answer_el = element.select_one(selector)
        if answer_el:
            # Check data-answer attribute first
            data_val = answer_el.get("data-answer")
            if data_val:
                return str(data_val).strip()
            text = answer_el.get_text(strip=True)
            # Clean: remove "Ответ:" or "Ответ" prefix
            text = re.sub(
                r"^Ответ\s*:?\s*", "", text, flags=re.IGNORECASE
            )
            if text:
                return text.strip()

    # Try data-answer attribute on the element itself
    data_answer = element.get("data-answer")
    if data_answer:
        return str(data_answer).strip()

    # Search all descendants for data-answer
    for el in element.find_all(attrs={"data-answer": True}):
        return str(el["data-answer"]).strip()

    # Look for text containing "Ответ:"
    for tag in element.find_all(string=re.compile(r"Ответ\s*:", re.IGNORECASE)):
        parent = tag.parent
        if parent:
            text = parent.get_text(strip=True)
            match = re.search(r"Ответ\s*:\s*(.+)", text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

    return None


def parse_problem_page(
    url: str, task_number: int, session: requests.Session
) -> ParsedProblem | None:
    """Parse a single problem page and extract problem data."""
    soup = fetch_page(url, session)
    if soup is None:
        return None

    # Shkolkovo problem content is typically in a main content container
    content_selectors = [
        ".task-content",
        ".problem-content",
        ".task-body",
        ".exercise-body",
        ".problem-text",
        "article .content",
        ".task_text",
        "main .text",
    ]

    content_el = None
    for selector in content_selectors:
        content_el = soup.select_one(selector)
        if content_el:
            break

    # Fallback: look for the main content area
    if content_el is None:
        content_el = soup.select_one("main") or soup.select_one(".main-content")

    if content_el is None:
        log.warning("Could not find problem content on %s", url)
        return None

    problem_text = extract_text_with_latex(content_el)
    if not problem_text or len(problem_text) < 10:
        log.warning("Problem text too short on %s", url)
        return None

    images = extract_images(content_el)
    answer = extract_answer(soup)

    problem = ParsedProblem(
        task_number=task_number,
        problem_text=problem_text,
        correct_answer=answer,
        problem_images=images,
        source_url=url,
    )
    problem.compute_hash()
    return problem


def parse_catalog_page(
    url: str, task_number: int, session: requests.Session
) -> tuple[list[str], str | None]:
    """Parse a catalog listing page.

    Returns (list of problem URLs, next page URL or None).
    """
    soup = fetch_page(url, session)
    if soup is None:
        return [], None

    problem_urls: list[str] = []

    # Look for links to individual problems
    link_selectors = [
        "a.task-link",
        "a.problem-link",
        ".task-list a",
        ".problems-list a",
        ".catalog-list a",
        ".exercise-link",
    ]

    found_links: list[Tag] = []
    for selector in link_selectors:
        found_links = soup.select(selector)
        if found_links:
            break

    # Fallback: look for all links that match a problem URL pattern
    if not found_links:
        # Shkolkovo problem URLs often contain numeric IDs
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Match patterns like /task/12345 or /problem/12345
            if re.search(
                r"/(task|problem|exercise|zadanie|zadacha)/\d+", str(href)
            ):
                found_links.append(a_tag)

    for link in found_links:
        href = link.get("href", "")
        if not href:
            continue
        if href.startswith("/"):
            href = BASE_URL + href
        elif not href.startswith("http"):
            href = BASE_URL + "/" + href
        if href not in problem_urls:
            problem_urls.append(href)

    # Find next page link
    next_url = None
    next_selectors = [
        "a.next",
        ".pagination a.next",
        'a[rel="next"]',
        ".pager .next a",
        ".pagination-next a",
    ]
    for selector in next_selectors:
        next_el = soup.select_one(selector)
        if next_el:
            next_href = next_el.get("href", "")
            if next_href:
                if next_href.startswith("/"):
                    next_url = BASE_URL + next_href
                elif not next_href.startswith("http"):
                    next_url = BASE_URL + "/" + next_href
                else:
                    next_url = next_href
            break

    # Also try page parameter pattern
    if not next_url and not found_links:
        # Try ?page=N pattern
        current_page = 1
        page_match = re.search(r"[?&]page=(\d+)", url)
        if page_match:
            current_page = int(page_match.group(1))
        # Check if there's content suggesting more pages
        if soup.find(string=re.compile(r"(Следующая|Далее|→|»)")):
            separator = "&" if "?" in url else "?"
            base = re.sub(r"[?&]page=\d+", "", url)
            next_url = f"{base}{separator}page={current_page + 1}"

    return problem_urls, next_url


def scrape_task(
    task_number: int,
    max_pages: int = 5,
    max_problems: int = 50,
) -> list[ParsedProblem]:
    """Scrape problems for a given task number from Shkolkovo.

    Args:
        task_number: EGE task number (1-19).
        max_pages: Maximum catalog pages to scrape.
        max_problems: Maximum problems to collect.

    Returns:
        List of parsed problems.
    """
    if not 1 <= task_number <= 19:
        log.error("Task number must be 1-19, got %d", task_number)
        return []

    catalog_url = CATALOG_URL.format(task_number=task_number)
    log.info("Starting scrape for task %d: %s", task_number, catalog_url)

    session = requests.Session()
    problems: list[ParsedProblem] = []
    seen_hashes: set[str] = set()
    current_url: str | None = catalog_url
    page = 0

    while current_url and page < max_pages and len(problems) < max_problems:
        page += 1
        log.info("Fetching catalog page %d: %s", page, current_url)

        problem_urls, next_url = parse_catalog_page(
            current_url, task_number, session
        )
        log.info("Found %d problem links on page %d", len(problem_urls), page)

        if not problem_urls:
            log.info("No problem links found on page %d, stopping.", page)
            break

        for prob_url in problem_urls:
            if len(problems) >= max_problems:
                break

            log.info("Parsing problem: %s", prob_url)
            time.sleep(REQUEST_DELAY)

            problem = parse_problem_page(prob_url, task_number, session)
            if problem is None:
                continue

            # Deduplicate by content hash
            if problem.content_hash in seen_hashes:
                log.debug("Duplicate problem skipped: %s", prob_url)
                continue

            seen_hashes.add(problem.content_hash)
            problems.append(problem)
            log.info(
                "Parsed problem %d (hash=%s...)",
                len(problems),
                problem.content_hash[:12],
            )

        current_url = next_url
        if current_url:
            time.sleep(REQUEST_DELAY)

    log.info(
        "Scrape complete for task %d: %d problems collected", task_number, len(problems)
    )
    return problems


def upload_to_supabase(problems: list[ParsedProblem]) -> int:
    """Upload parsed problems to Supabase (optional).

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
        .eq("source", "shkolkovo")
        .execute()
    )
    existing_hashes = {row["content_hash"] for row in (existing.data or []) if row.get("content_hash")}

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
                "No topic found for task_number %d, skipping", problem.task_number
            )
            skipped += 1
            continue

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

        try:
            client.table("problems").insert(row).execute()
            inserted += 1
        except Exception as e:
            log.warning("Failed to insert problem: %s", e)
            skipped += 1

    log.info("Upload complete. Added: %d, Skipped (duplicates): %d", inserted, skipped)
    return inserted


def save_to_json(problems: list[ParsedProblem], output_path: str) -> None:
    """Save parsed problems to a JSON file."""
    data = [asdict(p) for p in problems]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info("Saved %d problems to %s", len(problems), output_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse EGE math problems from 3.shkolkovo.online",
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
        help="Output JSON file path (default: shkolkovo_task_{N}.json)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum catalog pages to scrape (default: 5)",
    )
    parser.add_argument(
        "--max-problems",
        type=int,
        default=50,
        help="Maximum problems to collect (default: 50)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload parsed problems to Supabase",
    )

    args = parser.parse_args()

    if not 1 <= args.task_number <= 19:
        log.error("Task number must be between 1 and 19")
        sys.exit(1)

    problems = scrape_task(
        task_number=args.task_number,
        max_pages=args.max_pages,
        max_problems=args.max_problems,
    )

    if not problems:
        log.warning("No problems parsed. Check the site structure or selectors.")
        sys.exit(0)

    # Save to JSON
    output_path = args.output or f"shkolkovo_task_{args.task_number}.json"
    save_to_json(problems, output_path)

    # Optionally upload to Supabase
    if args.upload:
        upload_to_supabase(problems)


if __name__ == "__main__":
    main()

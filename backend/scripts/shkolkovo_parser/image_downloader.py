"""Download Shkolkovo problem images to deterministic local paths."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import Path
from urllib.parse import urlparse

import httpx

from scripts.shkolkovo_parser.config import repository_root, shkolkovo_data_dir
from scripts.shkolkovo_parser.fetcher import DEFAULT_USER_AGENT
from scripts.shkolkovo_parser.validator import ValidatedProblemRecord

CONTENT_TYPE_EXTENSIONS = {
    "image/gif": ".gif",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/svg+xml": ".svg",
    "image/webp": ".webp",
}
KNOWN_IMAGE_EXTENSIONS = frozenset(CONTENT_TYPE_EXTENSIONS.values())


@dataclass(frozen=True)
class ImageDownload:
    """One successfully downloaded problem image."""

    source_url: str
    local_path: Path
    repository_relative_path: str
    bytes_written: int


@dataclass(frozen=True)
class ImageDownloadResult:
    """Downloaded images and the updated dataset record."""

    record: ValidatedProblemRecord
    downloads: tuple[ImageDownload, ...]


def download_problem_images(
    record: ValidatedProblemRecord,
    *,
    client: httpx.Client | None = None,
    data_dir: Path | None = None,
    repository_root_path: Path | None = None,
) -> ImageDownloadResult:
    """Download all source problem images and attach local paths to a record."""
    repo_root = repository_root_path or repository_root()
    target_data_dir = data_dir or shkolkovo_data_dir()
    image_dir = target_data_dir / "images" / f"task_{record.task_number}"
    image_dir.mkdir(parents=True, exist_ok=True)

    http_client = client or httpx.Client(
        follow_redirects=True,
        headers={"User-Agent": DEFAULT_USER_AGENT},
        timeout=20.0,
    )
    owns_client = client is None

    downloads: list[ImageDownload] = []
    problem_images: list[str] = []
    seen_urls: set[str] = set()
    try:
        for source_url in record.source_image_urls:
            if source_url in seen_urls:
                continue
            seen_urls.add(source_url)

            response = http_client.get(source_url)
            response.raise_for_status()

            local_path = image_dir / image_filename_for_url(
                source_url,
                source_id=record.source_id,
                content_type=response.headers.get("content-type"),
            )
            local_path.write_bytes(response.content)
            relative_path = local_path.relative_to(repo_root).as_posix()
            problem_images.append(relative_path)
            downloads.append(
                ImageDownload(
                    source_url=source_url,
                    local_path=local_path,
                    repository_relative_path=relative_path,
                    bytes_written=len(response.content),
                ),
            )
    finally:
        if owns_client:
            http_client.close()

    return ImageDownloadResult(
        record=replace(record, problem_images=tuple(problem_images)),
        downloads=tuple(downloads),
    )


def image_filename_for_url(
    url: str,
    *,
    source_id: str | None = None,
    content_type: str | None = None,
) -> str:
    """Return the deterministic local filename for an image URL."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    stem = _safe_filename_part(source_id or "problem_image")
    extension = _extension_for_url(url) or _extension_for_content_type(content_type)
    return f"{stem}_{digest}{extension or '.bin'}"


def _extension_for_url(url: str) -> str | None:
    suffix = Path(urlparse(url).path).suffix.lower()
    if suffix in KNOWN_IMAGE_EXTENSIONS:
        return suffix
    return None


def _extension_for_content_type(content_type: str | None) -> str | None:
    if content_type is None:
        return None
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    return CONTENT_TYPE_EXTENSIONS.get(media_type)


def _safe_filename_part(value: str) -> str:
    safe_value = "".join(char if char.isalnum() else "_" for char in value).strip("_")
    return safe_value or "problem_image"

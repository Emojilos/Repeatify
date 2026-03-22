"""Download and store problem images locally and in Supabase Storage.

Provides helpers used by shkolkovo_parser, math100_parser, and normalizer
to download external images, save them to a local directory, and optionally
upload them to a Supabase Storage bucket.

Local images are saved under:
  tools/parsers/images/{source}/{task_number}/{content_hash}_{idx}.{ext}

Supabase Storage path:
  problem-images/{source}/{task_number}/{content_hash}_{idx}.{ext}
"""

from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse

import requests

log = logging.getLogger(__name__)

_project_root = Path(__file__).resolve().parent.parent.parent

IMAGES_DIR = Path(__file__).resolve().parent / "images"

STORAGE_BUCKET = "problem-images"

# Allowed image extensions
_ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}

# Timeout for image downloads
_DOWNLOAD_TIMEOUT = 15


def _guess_extension(url: str, content_type: str | None = None) -> str:
    """Guess file extension from URL path or Content-Type header."""
    parsed = urlparse(url)
    ext = Path(parsed.path).suffix.lower()
    if ext in _ALLOWED_EXTENSIONS:
        return ext

    if content_type:
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        if guessed and guessed in _ALLOWED_EXTENSIONS:
            return guessed

    return ".png"


def _make_filename(
    source: str, task_number: int, content_hash: str, idx: int, ext: str
) -> str:
    """Build a deterministic filename for an image."""
    short_hash = content_hash[:16] if content_hash else "nohash"
    return f"{short_hash}_{idx}{ext}"


def download_images(
    image_urls: list[str],
    source: str,
    task_number: int,
    content_hash: str,
    session: requests.Session | None = None,
) -> list[str]:
    """Download images from URLs and save them locally.

    Args:
        image_urls: List of absolute image URLs.
        source: Source identifier (e.g. "shkolkovo", "math100").
        task_number: EGE task number (1-19).
        content_hash: Content hash of the problem (for filenames).
        session: Optional requests session (reuses connections).

    Returns:
        List of local file paths (relative to project root) for
        successfully downloaded images.  Failed downloads are skipped
        with a warning.
    """
    if not image_urls:
        return []

    sess = session or requests.Session()
    dest_dir = IMAGES_DIR / source / str(task_number)
    dest_dir.mkdir(parents=True, exist_ok=True)

    local_paths: list[str] = []

    for idx, url in enumerate(image_urls):
        try:
            resp = sess.get(url, timeout=_DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()
        except Exception as e:
            log.warning("Failed to download image %s: %s", url, e)
            continue

        ct = resp.headers.get("Content-Type")
        ext = _guess_extension(url, ct)
        filename = _make_filename(source, task_number, content_hash, idx, ext)
        filepath = dest_dir / filename

        # Skip if already downloaded (idempotent)
        if filepath.exists() and filepath.stat().st_size > 0:
            rel = str(filepath.relative_to(_project_root))
            local_paths.append(rel)
            log.debug("Image already exists: %s", rel)
            continue

        try:
            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        except Exception as e:
            log.warning("Failed to save image %s: %s", filepath, e)
            if filepath.exists():
                filepath.unlink(missing_ok=True)
            continue

        rel = str(filepath.relative_to(_project_root))
        local_paths.append(rel)
        log.info("Downloaded image: %s -> %s", url, rel)

    return local_paths


def upload_images_to_storage(
    local_paths: list[str],
    source: str,
    task_number: int,
) -> list[str]:
    """Upload locally downloaded images to Supabase Storage.

    Args:
        local_paths: List of local file paths (relative to project root).
        source: Source identifier.
        task_number: EGE task number.

    Returns:
        List of public URLs from Supabase Storage.
        Falls back to local paths on failure.
    """
    from dotenv import load_dotenv
    from supabase import create_client

    load_dotenv(_project_root / ".env")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        log.error("SUPABASE_URL and SUPABASE_SERVICE_KEY required for storage upload")
        return local_paths

    client = create_client(url, key)
    storage_urls: list[str] = []

    for local_path in local_paths:
        abs_path = _project_root / local_path
        if not abs_path.exists():
            log.warning("Local file not found: %s", abs_path)
            storage_urls.append(local_path)
            continue

        filename = abs_path.name
        storage_path = f"{source}/{task_number}/{filename}"

        content_type = mimetypes.guess_type(str(abs_path))[0] or "image/png"

        try:
            with open(abs_path, "rb") as f:
                data = f.read()

            client.storage.from_(STORAGE_BUCKET).upload(
                path=storage_path,
                file=data,
                file_options={"content-type": content_type, "upsert": "true"},
            )

            public_url = client.storage.from_(STORAGE_BUCKET).get_public_url(
                storage_path
            )
            storage_urls.append(public_url)
            log.info("Uploaded to storage: %s -> %s", local_path, storage_path)

        except Exception as e:
            log.warning("Failed to upload %s to storage: %s", storage_path, e)
            storage_urls.append(local_path)

    return storage_urls


def process_images(
    image_urls: list[str],
    source: str,
    task_number: int,
    content_hash: str,
    session: requests.Session | None = None,
    upload: bool = False,
) -> list[str]:
    """Download images and optionally upload to Supabase Storage.

    This is the main entry point for parsers. It:
    1. Downloads images from external URLs to local disk
    2. Optionally uploads them to Supabase Storage
    3. Returns the final paths/URLs to store in problem_images

    Args:
        image_urls: External image URLs extracted from the page.
        source: Source identifier (e.g. "shkolkovo").
        task_number: EGE task number.
        content_hash: Problem content hash (for filenames).
        session: Optional requests session.
        upload: If True, also upload to Supabase Storage.

    Returns:
        List of paths/URLs: Supabase public URLs if upload=True,
        otherwise local relative paths.
    """
    if not image_urls:
        return []

    local_paths = download_images(
        image_urls, source, task_number, content_hash, session
    )

    if not local_paths:
        return []

    if upload:
        return upload_images_to_storage(local_paths, source, task_number)

    return local_paths

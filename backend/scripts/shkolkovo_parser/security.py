"""URL and local path safety helpers for parser-generated artifacts."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse


class ParserSecurityError(ValueError):
    """Raised when parser input would escape the public/local safety contract."""


def validate_public_http_url(url: str, *, context: str = "URL") -> str:
    """Return a stripped public HTTP(S) URL or raise a diagnostic error."""
    normalized_url = url.strip()
    parsed = urlparse(normalized_url)
    if parsed.scheme not in {"http", "https"}:
        msg = f"{context} must use http or https: {url!r}"
        raise ParserSecurityError(msg)
    if not parsed.netloc:
        msg = f"{context} must include a public host: {url!r}"
        raise ParserSecurityError(msg)
    return normalized_url


def safe_child_file(base_dir: Path, filename: str, *, context: str = "file") -> Path:
    """Return a child file path, rejecting absolute paths and traversal."""
    filename_path = Path(filename)
    if filename_path.is_absolute() or len(filename_path.parts) != 1:
        msg = f"{context} name must be a plain filename: {filename!r}"
        raise ParserSecurityError(msg)

    resolved_base = base_dir.resolve()
    candidate = (resolved_base / filename_path.name).resolve()
    if not candidate.is_relative_to(resolved_base):
        msg = f"{context} path escapes {base_dir}: {filename!r}"
        raise ParserSecurityError(msg)
    return candidate

"""HTTP-first fetch layer with retries and local HTML snapshots."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx

from scripts.shkolkovo_parser.config import shkolkovo_data_path

DEFAULT_USER_AGENT = "Repeatify-Shkolkovo-Parser/0.1"
TEMPORARY_STATUS_CODES = frozenset({500, 502, 503, 504})


@dataclass(frozen=True)
class FetchResult:
    """Successful HTML fetch result and its saved snapshot."""

    url: str
    status_code: int
    html: str
    snapshot_path: Path
    attempts: int


class FetchError(RuntimeError):
    """Raised when a page cannot be fetched after configured attempts."""

    def __init__(
        self,
        message: str,
        *,
        url: str,
        attempts: int,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.url = url
        self.attempts = attempts
        self.status_code = status_code


class ShkolkovoFetcher:
    """Fetch public HTML pages and save repository-local snapshots."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        snapshot_dir: Path | None = None,
        delay: float = 1.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if delay < 0:
            raise ValueError("delay must be at least 0")
        if max_retries < 0:
            raise ValueError("max_retries must be at least 0")
        if backoff_factor < 0:
            raise ValueError("backoff_factor must be at least 0")

        self._client = client or httpx.Client(
            follow_redirects=True,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=20.0,
        )
        self._owns_client = client is None
        self._snapshot_dir = snapshot_dir
        self._delay = delay
        self._max_retries = max_retries
        self._backoff_factor = backoff_factor
        self._sleep = sleep
        self._requests_started = 0

    def fetch(self, url: str, *, snapshot_name: str | None = None) -> FetchResult:
        """Fetch one HTML URL, retry temporary failures, and write a snapshot."""
        max_attempts = self._max_retries + 1
        last_status_code: int | None = None
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            self._wait_before_request()
            try:
                response = self._client.get(url)
            except httpx.RequestError as exc:
                last_error = exc
                if attempt < max_attempts:
                    self._wait_before_retry(attempt)
                    continue
                message = (
                    f"temporary request error for {url!r} after "
                    f"{attempt} attempt(s): {exc}"
                )
                raise FetchError(message, url=url, attempts=attempt) from exc

            last_status_code = response.status_code
            if response.status_code in TEMPORARY_STATUS_CODES:
                if attempt < max_attempts:
                    self._wait_before_retry(attempt)
                    continue
                message = (
                    f"temporary HTTP {response.status_code} for {url!r} after "
                    f"{attempt} attempt(s)"
                )
                raise FetchError(
                    message,
                    url=url,
                    attempts=attempt,
                    status_code=response.status_code,
                )

            if response.is_error:
                message = (
                    f"HTTP {response.status_code} for {url!r} after "
                    f"{attempt} attempt(s)"
                )
                raise FetchError(
                    message,
                    url=url,
                    attempts=attempt,
                    status_code=response.status_code,
                )

            snapshot_path = self._write_snapshot(
                url,
                response.text,
                snapshot_name=snapshot_name,
            )
            return FetchResult(
                url=str(response.url),
                status_code=response.status_code,
                html=response.text,
                snapshot_path=snapshot_path,
                attempts=attempt,
            )

        message = f"failed to fetch {url!r} after {max_attempts} attempt(s)"
        if last_error is not None:
            message = f"{message}: {last_error}"
        raise FetchError(
            message,
            url=url,
            attempts=max_attempts,
            status_code=last_status_code,
        )

    def close(self) -> None:
        """Close an internally owned HTTP client."""
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> ShkolkovoFetcher:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _wait_before_request(self) -> None:
        if self._requests_started > 0 and self._delay > 0:
            self._sleep(self._delay)
        self._requests_started += 1

    def _wait_before_retry(self, attempt: int) -> None:
        retry_delay = self._backoff_factor * attempt
        if retry_delay > 0:
            self._sleep(retry_delay)

    def _write_snapshot(
        self,
        url: str,
        html: str,
        *,
        snapshot_name: str | None,
    ) -> Path:
        snapshot_dir = self._snapshot_dir or shkolkovo_data_path("html")
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        filename = snapshot_name or snapshot_filename_for_url(url)
        path = snapshot_dir / filename
        path.write_text(html, encoding="utf-8")
        return path


def snapshot_filename_for_url(url: str) -> str:
    """Build a stable, filesystem-safe HTML snapshot filename."""
    parsed = urlparse(url)
    base = "_".join(part for part in (parsed.netloc, parsed.path.strip("/")) if part)
    safe_base = "".join(char if char.isalnum() else "_" for char in base).strip("_")
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    if not safe_base:
        safe_base = "page"
    return f"{safe_base}_{digest}.html"

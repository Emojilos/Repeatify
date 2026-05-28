"""Tests for the Shkolkovo parser HTTP fetch layer."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from scripts.shkolkovo_parser.fetcher import (
    FetchError,
    ShkolkovoFetcher,
    snapshot_filename_for_url,
)


def test_fetcher_downloads_html_and_writes_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("https://example.test/public/problem/1")
        return httpx.Response(200, text="<html><h1>Problem</h1></html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(client=client, snapshot_dir=tmp_path, delay=0)

    result = fetcher.fetch("https://example.test/public/problem/1")

    assert result.status_code == 200
    assert result.html == "<html><h1>Problem</h1></html>"
    assert result.attempts == 1
    assert result.snapshot_path.parent == tmp_path
    assert result.snapshot_path.read_text(encoding="utf-8") == result.html


def test_snapshot_filename_is_stable_and_html_scoped() -> None:
    url = "https://example.test/public/problem/1?variant=2"

    assert snapshot_filename_for_url(url) == snapshot_filename_for_url(url)
    assert snapshot_filename_for_url(url).startswith("example_test_public_problem_1_")
    assert snapshot_filename_for_url(url).endswith(".html")


def test_fetcher_retries_temporary_http_errors(tmp_path: Path) -> None:
    responses = [503, 200]
    sleeps: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        status_code = responses.pop(0)
        return httpx.Response(status_code, text=f"<html>{status_code}</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(
        client=client,
        snapshot_dir=tmp_path,
        delay=0,
        max_retries=1,
        backoff_factor=0.25,
        sleep=sleeps.append,
    )

    result = fetcher.fetch("https://example.test/temporary")

    assert result.status_code == 200
    assert result.attempts == 2
    assert sleeps == [0.25]
    assert result.snapshot_path.read_text(encoding="utf-8") == "<html>200</html>"


def test_fetcher_reports_exhausted_temporary_http_errors(tmp_path: Path) -> None:
    attempts = 0

    def handler(_request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, text="<html>temporary</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(
        client=client,
        snapshot_dir=tmp_path,
        delay=0,
        max_retries=2,
        backoff_factor=0,
    )

    with pytest.raises(FetchError) as exc_info:
        fetcher.fetch("https://example.test/temporary")

    assert attempts == 3
    assert exc_info.value.attempts == 3
    assert exc_info.value.status_code == 503
    assert "temporary HTTP 503" in str(exc_info.value)
    assert not list(tmp_path.iterdir())


def test_fetcher_applies_delay_between_html_requests(tmp_path: Path) -> None:
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=f"<html>{request.url.path}</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(
        client=client,
        snapshot_dir=tmp_path,
        delay=0.75,
        max_retries=0,
        sleep=sleeps.append,
    )

    fetcher.fetch("https://example.test/first")
    fetcher.fetch("https://example.test/second")

    assert sleeps == [0.75]

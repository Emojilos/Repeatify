"""Tests for the Shkolkovo parser HTTP fetch layer."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from scripts.shkolkovo_parser.fetcher import (
    CollectionStoppedError,
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


def test_fetcher_stops_collection_on_rate_limit(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="<html>too many requests</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(client=client, snapshot_dir=tmp_path, delay=0)

    with pytest.raises(CollectionStoppedError) as exc_info:
        fetcher.fetch("https://example.test/rate-limited")

    assert exc_info.value.reason == "rate_limited"
    assert exc_info.value.status_code == 429
    assert exc_info.value.to_error_record() == {
        "url": "https://example.test/rate-limited",
        "attempts": 1,
        "status_code": 429,
        "message": str(exc_info.value),
        "reason": "rate_limited",
        "stop_collection": True,
    }
    assert not list(tmp_path.iterdir())


def test_fetcher_stops_collection_after_forbidden_series(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="<html>forbidden</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(
        client=client,
        snapshot_dir=tmp_path,
        delay=0,
        forbidden_stop_threshold=2,
    )

    with pytest.raises(FetchError) as first_error:
        fetcher.fetch("https://example.test/forbidden-1")

    assert not isinstance(first_error.value, CollectionStoppedError)

    with pytest.raises(CollectionStoppedError) as stop_error:
        fetcher.fetch("https://example.test/forbidden-2")

    assert stop_error.value.reason == "forbidden_series"
    assert stop_error.value.status_code == 403
    assert stop_error.value.to_error_record()["stop_collection"] is True
    assert not list(tmp_path.iterdir())


def test_fetcher_resets_forbidden_series_after_success(tmp_path: Path) -> None:
    responses = [403, 200, 403]

    def handler(_request: httpx.Request) -> httpx.Response:
        status_code = responses.pop(0)
        return httpx.Response(status_code, text=f"<html>{status_code}</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(
        client=client,
        snapshot_dir=tmp_path,
        delay=0,
        forbidden_stop_threshold=2,
    )

    with pytest.raises(FetchError):
        fetcher.fetch("https://example.test/forbidden-1")
    assert fetcher.fetch("https://example.test/ok").status_code == 200
    with pytest.raises(FetchError) as second_error:
        fetcher.fetch("https://example.test/forbidden-2")

    assert not isinstance(second_error.value, CollectionStoppedError)


def test_fetcher_stops_collection_on_captcha_html(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        html = "<html><title>Checking your browser</title><div>captcha</div></html>"
        return httpx.Response(200, text=html)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(client=client, snapshot_dir=tmp_path, delay=0)

    with pytest.raises(CollectionStoppedError) as exc_info:
        fetcher.fetch("https://example.test/browser-check")

    assert exc_info.value.reason == "captcha_or_browser_check"
    assert exc_info.value.status_code == 200
    assert "detected captcha_or_browser_check" in str(exc_info.value)
    assert not list(tmp_path.iterdir())


def test_fetcher_rejects_clients_with_credentials(tmp_path: Path) -> None:
    clients = [
        httpx.Client(headers={"Authorization": "Bearer secret"}),
        httpx.Client(headers={"Cookie": "session=secret"}),
        httpx.Client(cookies={"session": "secret"}),
        httpx.Client(auth=("user", "password")),
    ]

    try:
        for client in clients:
            with pytest.raises(ValueError, match="not allowed"):
                ShkolkovoFetcher(client=client, snapshot_dir=tmp_path, delay=0)
    finally:
        for client in clients:
            client.close()


def test_fetcher_sends_no_credentials_by_default(tmp_path: Path) -> None:
    seen_headers: list[httpx.Headers] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.append(request.headers)
        return httpx.Response(200, text="<html>public</html>")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    fetcher = ShkolkovoFetcher(client=client, snapshot_dir=tmp_path, delay=0)

    fetcher.fetch("https://example.test/public")

    assert "authorization" not in seen_headers[0]
    assert "cookie" not in seen_headers[0]
    assert "proxy-authorization" not in seen_headers[0]

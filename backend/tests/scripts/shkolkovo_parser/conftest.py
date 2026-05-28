"""Shared guards for Shkolkovo fixture-based integration tests."""

from __future__ import annotations

import socket
from typing import Any

import httpx
import pytest


@pytest.fixture(autouse=True)
def deny_live_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail the fixture suite if a test reaches outside local fixtures."""

    def fail_socket_connection(*_args: Any, **_kwargs: Any) -> None:
        pytest.fail("fixture-based parser tests must not open network sockets")

    def fail_http_request(
        _transport: httpx.HTTPTransport,
        request: httpx.Request,
    ) -> httpx.Response:
        pytest.fail(f"fixture-based parser tests made live HTTP request: {request.url}")

    monkeypatch.setattr(socket, "create_connection", fail_socket_connection)
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", fail_http_request)

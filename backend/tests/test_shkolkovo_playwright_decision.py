"""Tests for the documented Playwright fallback decision."""

from __future__ import annotations

import tomllib
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
PACKAGE_DIR = BACKEND_DIR / "scripts" / "shkolkovo_parser"
CHROMIUM_INSTALL_COMMAND = "uv run --group parser playwright install chromium"


def test_parser_group_includes_playwright_for_browser_required_discovery() -> None:
    pyproject = tomllib.loads(
        (BACKEND_DIR / "pyproject.toml").read_text(encoding="utf-8"),
    )

    parser_group = pyproject["dependency-groups"]["parser"]

    assert any(dependency.startswith("playwright>=") for dependency in parser_group)


def test_playwright_chromium_install_command_is_documented() -> None:
    readme = (PACKAGE_DIR / "README.md").read_text(encoding="utf-8")
    discovery = (PACKAGE_DIR / "DISCOVERY.md").read_text(encoding="utf-8")

    assert CHROMIUM_INSTALL_COMMAND in readme
    assert CHROMIUM_INSTALL_COMMAND in discovery
    assert "browser-backed fallback" in discovery

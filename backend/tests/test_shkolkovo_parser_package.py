"""Tests for the Shkolkovo parser package scaffold."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import scripts.shkolkovo_parser as shkolkovo_parser


def test_shkolkovo_parser_package_imports() -> None:
    assert shkolkovo_parser.__version__ == "0.1.0"


def test_shkolkovo_parser_module_help_runs() -> None:
    backend_dir = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-m", "scripts.shkolkovo_parser", "--help"],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Shkolkovo" in result.stdout
    assert "--version" in result.stdout

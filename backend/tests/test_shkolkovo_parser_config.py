"""Tests for repository-relative Shkolkovo parser paths."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from scripts.shkolkovo_parser.config import (
    DATA_RAW_RELATIVE_PATH,
    repository_root,
    shkolkovo_data_dir,
    shkolkovo_data_path,
)


def test_repository_root_and_data_dir_are_repo_relative() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    assert repository_root() == repo_root
    assert shkolkovo_data_dir() == repo_root / "data/raw/shkolkovo"
    assert DATA_RAW_RELATIVE_PATH == Path("data/raw/shkolkovo")


def test_data_path_creates_parent_under_repo_root() -> None:
    path = shkolkovo_data_path("html", "path_check.html", create_parent=True)

    assert path == repository_root() / "data/raw/shkolkovo/html/path_check.html"
    assert path.parent.is_dir()


def test_repository_relative_paths_match_from_repo_root_and_backend() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"
    code = (
        "from scripts.shkolkovo_parser.config import repository_root, "
        "shkolkovo_data_dir; "
        "print(repository_root()); print(shkolkovo_data_dir())"
    )
    env = {
        **os.environ,
        "PYTHONPATH": str(backend_dir),
    }

    root_result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=repo_root,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )
    backend_result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_dir,
        capture_output=True,
        check=False,
        env=env,
        text=True,
    )

    assert root_result.returncode == 0, root_result.stderr
    assert backend_result.returncode == 0, backend_result.stderr
    assert root_result.stdout == backend_result.stdout
    assert str(repo_root / "data/raw/shkolkovo") in root_result.stdout

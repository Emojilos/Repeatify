"""Repository-relative paths for Shkolkovo parser artifacts."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
DATA_RAW_RELATIVE_PATH = Path("data/raw/shkolkovo")


@lru_cache(maxsize=1)
def repository_root() -> Path:
    """Return the repository root regardless of the process working directory."""
    for candidate in (PACKAGE_DIR, *PACKAGE_DIR.parents):
        if (candidate / ".git").exists() and (candidate / "backend").is_dir():
            return candidate

    msg = f"Could not locate repository root from {PACKAGE_DIR}"
    raise RuntimeError(msg)


def shkolkovo_data_dir(*, create: bool = True) -> Path:
    """Return the generated dataset directory for Shkolkovo parser outputs."""
    data_dir = repository_root() / DATA_RAW_RELATIVE_PATH
    if create:
        data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def shkolkovo_data_path(*parts: str, create_parent: bool = False) -> Path:
    """Build a path under data/raw/shkolkovo."""
    path = shkolkovo_data_dir(create=True) / Path(*parts)
    if create_parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path

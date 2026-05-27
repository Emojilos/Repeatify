"""Command-line entry point for the Shkolkovo parser package."""

from __future__ import annotations

from collections.abc import Sequence

from scripts.shkolkovo_parser.cli import main as run_cli


def main(argv: Sequence[str] | None = None) -> int:
    """Run the parser CLI."""
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())

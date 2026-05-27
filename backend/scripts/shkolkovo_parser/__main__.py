"""Command-line entry point for the Shkolkovo parser package."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from scripts.shkolkovo_parser import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the current CLI surface for the parser package."""
    parser = argparse.ArgumentParser(
        prog="python -m scripts.shkolkovo_parser",
        description="Collect public Shkolkovo problem data.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the parser CLI."""
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

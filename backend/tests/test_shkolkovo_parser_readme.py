"""Documentation coverage for the Shkolkovo parser README."""

from __future__ import annotations

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
README = BACKEND_DIR / "scripts" / "shkolkovo_parser" / "README.md"
TEST_COMMAND = "uv run --group parser python -m scripts.shkolkovo_parser --mode test"
ALL_COMMAND = "uv run --group parser python -m scripts.shkolkovo_parser --mode all"
SNAPSHOT_COMMAND = (
    "uv run --group parser python -m scripts.shkolkovo_parser "
    "--mode snapshots --task-number 6 --snapshot-dir"
)


def test_readme_documents_parser_path_commands_and_outputs() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "backend/scripts/shkolkovo_parser/" in readme
    assert TEST_COMMAND in readme
    assert f"{TEST_COMMAND} --task-number 6" in readme
    assert f"{TEST_COMMAND} --task-number 6 --per-subcategory 1" in readme
    assert ALL_COMMAND in readme
    assert "offline all-mode run over bundled fixtures" in readme
    assert "not approval to run a full live" in readme
    assert SNAPSHOT_COMMAND in readme
    assert "reads local `.html` files without network access" in readme
    assert "problem_pages/*.html" in readme
    assert (
        "uv run --group parser python -m scripts.shkolkovo_parser "
        "--task-number 6 --max-pages 1 --max-problems 3 --debug"
    ) in readme
    assert "data/raw/shkolkovo/" in readme
    assert "task_N.json" in readme
    assert "task_N_errors.json" in readme
    assert "task_N_report.json" in readme


def test_readme_documents_access_limits_and_playwright_note() -> None:
    readme = README.read_text(encoding="utf-8")

    assert "uv run --group parser playwright install chromium" in readme
    assert "does not import data into Supabase" in readme
    assert "public unauthenticated content" in readme
    assert "TASK-032 remains gated by the live smoke" in readme
    assert "It must not use\ncredentials" in readme
    assert "CAPTCHA" in readme

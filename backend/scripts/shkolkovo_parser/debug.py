"""Write local debug artifacts for Shkolkovo parser runs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.shkolkovo_parser.catalog_parser import ParsedCatalog
from scripts.shkolkovo_parser.config import shkolkovo_data_dir
from scripts.shkolkovo_parser.security import safe_child_file
from scripts.shkolkovo_parser.validator import (
    ProblemValidationError,
    ValidatedProblemRecord,
)


@dataclass(frozen=True)
class DebugArtifactResult:
    """Files written for one debug-enabled task run."""

    debug_dir: Path
    files: tuple[Path, ...]


def write_debug_artifacts(
    *,
    task_number: int,
    catalog_html: str,
    problem_pages: dict[str, str],
    catalog: ParsedCatalog,
    records: tuple[ValidatedProblemRecord, ...],
    errors: tuple[ProblemValidationError, ...],
    output_dir: Path | None = None,
) -> DebugArtifactResult:
    """Write raw and intermediate task artifacts under debug/task_N/."""
    debug_dir = _debug_task_dir(task_number=task_number, output_dir=output_dir)
    problem_dir = debug_dir / "problem_pages"
    problem_dir.mkdir(parents=True, exist_ok=True)

    files = [
        _write_text(debug_dir / "catalog_raw.html", catalog_html),
        _write_json(debug_dir / "catalog_parsed.json", _catalog_payload(catalog)),
        _write_json(
            debug_dir / "validated_records.json",
            [record.to_dataset_record() for record in records],
        ),
        _write_json(
            debug_dir / "validation_errors.json",
            [error.to_error_record() for error in errors],
        ),
    ]
    for source_id, html in sorted(problem_pages.items()):
        files.append(
            _write_text(
                safe_child_file(
                    problem_dir,
                    f"{_safe_debug_stem(source_id)}_raw.html",
                    context="debug problem snapshot",
                ),
                html,
            ),
        )

    return DebugArtifactResult(debug_dir=debug_dir, files=tuple(files))


def _debug_task_dir(*, task_number: int, output_dir: Path | None) -> Path:
    target_dir = output_dir or shkolkovo_data_dir()
    debug_dir = target_dir / "debug" / f"task_{task_number}"
    debug_dir.mkdir(parents=True, exist_ok=True)
    return debug_dir


def _catalog_payload(catalog: ParsedCatalog) -> dict[str, Any]:
    return {
        "problems": [
            {
                "task_number": problem.task_number,
                "category": problem.category,
                "subcategory": problem.subcategory,
                "source_url": problem.source_url,
                "source_id": problem.source_id,
            }
            for problem in catalog.problems
        ],
        "errors": [
            {
                "source_url": error.source_url,
                "reason": error.reason,
                "message": error.message,
            }
            for error in catalog.errors
        ],
    }


def _write_json(path: Path, payload: Any) -> Path:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _write_text(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _safe_debug_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return stem or "unknown"

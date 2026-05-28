"""Validation for parsed Shkolkovo problem records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scripts.shkolkovo_parser.catalog_parser import MAX_TASK_NUMBER, MIN_TASK_NUMBER
from scripts.shkolkovo_parser.problem_parser import ParsedProblem

ParseStatus = Literal["ok", "partial"]

MISSING_CORRECT_ANSWER = "missing_correct_answer"
MISSING_PROBLEM_TEXT = "missing_problem_text"
INVALID_TASK_NUMBER = "invalid_task_number"


@dataclass(frozen=True)
class ValidatedProblemRecord:
    """Problem record that is usable for the main task_N.json dataset."""

    task_number: int
    problem_text: str
    correct_answer: str | None
    source_url: str
    source_id: str | None
    category: str | None
    subcategory: str | None
    parse_status: ParseStatus
    parse_errors: tuple[str, ...]
    source_image_urls: tuple[str, ...] = ()

    def to_dataset_record(self) -> dict[str, object]:
        """Return a JSON-ready representation for task_N.json."""
        return {
            "task_number": self.task_number,
            "problem_text": self.problem_text,
            "correct_answer": self.correct_answer,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "category": self.category,
            "subcategory": self.subcategory,
            "source_image_urls": list(self.source_image_urls),
            "parse_status": self.parse_status,
            "parse_errors": list(self.parse_errors),
        }


@dataclass(frozen=True)
class ProblemValidationError:
    """Problem page that must be written to task_N_errors.json."""

    task_number: int | None
    source_url: str
    source_id: str | None
    parse_errors: tuple[str, ...]
    message: str

    def to_error_record(self) -> dict[str, object]:
        """Return a JSON-ready representation for task_N_errors.json."""
        return {
            "task_number": self.task_number,
            "source_url": self.source_url,
            "source_id": self.source_id,
            "parse_errors": list(self.parse_errors),
            "message": self.message,
        }


@dataclass(frozen=True)
class ProblemValidationResult:
    """Validation result with either a dataset record or an error record."""

    record: ValidatedProblemRecord | None
    error: ProblemValidationError | None

    @property
    def is_usable(self) -> bool:
        """Whether the parsed page belongs in the main dataset."""
        return self.record is not None


def validate_problem(
    problem: ParsedProblem,
    *,
    task_number: int,
    category: str | None = None,
    subcategory: str | None = None,
) -> ProblemValidationResult:
    """Validate parsed problem data for dataset export."""
    task_number_error = _validate_task_number(task_number)
    if task_number_error is not None:
        return ProblemValidationResult(
            record=None,
            error=ProblemValidationError(
                task_number=task_number,
                source_url=problem.source_url,
                source_id=problem.source_id,
                parse_errors=(task_number_error,),
                message=_error_message(task_number_error),
            ),
        )

    problem_text = problem.problem_text.strip()
    if not problem_text:
        return ProblemValidationResult(
            record=None,
            error=ProblemValidationError(
                task_number=task_number,
                source_url=problem.source_url,
                source_id=problem.source_id,
                parse_errors=(MISSING_PROBLEM_TEXT,),
                message=_error_message(MISSING_PROBLEM_TEXT),
            ),
        )

    correct_answer = _clean_optional_text(problem.correct_answer)
    parse_errors: tuple[str, ...] = ()
    parse_status: ParseStatus = "ok"
    if correct_answer is None:
        parse_errors = (MISSING_CORRECT_ANSWER,)
        parse_status = "partial"

    return ProblemValidationResult(
        record=ValidatedProblemRecord(
            task_number=task_number,
            problem_text=problem_text,
            correct_answer=correct_answer,
            source_url=problem.source_url,
            source_id=problem.source_id,
            category=_clean_optional_text(category),
            subcategory=_clean_optional_text(subcategory),
            parse_status=parse_status,
            parse_errors=parse_errors,
            source_image_urls=tuple(problem.source_image_urls),
        ),
        error=None,
    )


def _validate_task_number(task_number: int) -> str | None:
    if MIN_TASK_NUMBER <= task_number <= MAX_TASK_NUMBER:
        return None
    return INVALID_TASK_NUMBER


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _error_message(reason: str) -> str:
    if reason == MISSING_CORRECT_ANSWER:
        return "problem page has usable text but no public correct answer"
    if reason == MISSING_PROBLEM_TEXT:
        return "problem page has no usable problem text"
    if reason == INVALID_TASK_NUMBER:
        return (
            f"problem task number is outside "
            f"{MIN_TASK_NUMBER}-{MAX_TASK_NUMBER}"
        )
    return "problem page is invalid"

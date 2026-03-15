from enum import Enum

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    basic = "basic"
    medium = "medium"
    hard = "hard"
    olympiad = "olympiad"


class SelfAssessment(str, Enum):
    again = "again"
    hard = "hard"
    good = "good"
    easy = "easy"


class ProblemListItem(BaseModel):
    id: str
    topic_id: str
    task_number: int
    difficulty: str
    problem_text: str
    problem_images: list[str] | None = None
    hints: list[str] | None = None
    source: str | None = None
    max_points: int | None = None
    prototype_id: str | None = None
    source_url: str | None = None
    content_hash: str | None = None


class ProblemDetail(BaseModel):
    """Single problem — correct_answer is NEVER included before attempt."""

    id: str
    topic_id: str
    task_number: int
    difficulty: str
    problem_text: str
    problem_images: list[str] | None = None
    hints: list[str] | None = None
    source: str | None = None
    prototype_id: str | None = None
    source_url: str | None = None
    content_hash: str | None = None


class AttemptRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=50)
    time_spent_seconds: int = Field(..., ge=0, le=36000)
    self_assessment: SelfAssessment


class AttemptResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    solution_markdown: str | None = None
    xp_earned: int
    new_level_reached: int | None = None
    attempt_id: str


class ProblemListResponse(BaseModel):
    items: list[ProblemListItem]
    total: int
    page: int
    page_size: int

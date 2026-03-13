from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.problems import SelfAssessment


class SRSCardResponse(BaseModel):
    """A single SRS card in a session."""

    card_id: str
    problem_id: str
    topic_id: str
    topic_title: str | None = None
    task_number: int
    card_type: str
    problem_text: str
    problem_images: list[str] | None = None
    hints: list[str] | None = None
    difficulty: str | None = None
    ease_factor: float
    interval_days: float
    repetition_count: int


class SRSSessionResponse(BaseModel):
    """Response for GET /api/srs/session."""

    cards: list[SRSCardResponse]
    total_due: int


class SRSReviewRequest(BaseModel):
    """Request for POST /api/srs/review."""

    card_id: str
    answer: str = Field("", max_length=50)
    time_spent_seconds: int = Field(0, ge=0, le=36000)
    self_assessment: SelfAssessment


class SRSReviewResponse(BaseModel):
    """Response for POST /api/srs/review."""

    is_correct: bool
    correct_answer: str | None = None
    solution_markdown: str | None = None
    xp_earned: int
    new_level_reached: int | None = None
    next_review_date: str
    new_interval: float
    new_ease_factor: float

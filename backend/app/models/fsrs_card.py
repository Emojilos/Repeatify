from enum import Enum

from pydantic import BaseModel, Field


class FSRSCardType(str, Enum):
    problem = "problem"
    concept = "concept"
    formula = "formula"


class FSRSCardState(str, Enum):
    new = "new"
    learning = "learning"
    review = "review"
    relearning = "relearning"


class FSRSCardBase(BaseModel):
    problem_id: str | None = None
    prototype_id: str | None = None
    card_type: FSRSCardType


class FSRSCardResponse(BaseModel):
    id: str
    user_id: str
    problem_id: str | None = None
    prototype_id: str | None = None
    card_type: str
    difficulty: float
    stability: float
    due: str
    last_review: str | None = None
    reps: int
    lapses: int
    state: str
    scheduled_days: int | None = None
    elapsed_days: int | None = None
    created_at: str | None = None
    # Enriched fields for session display
    problem_text: str | None = None
    problem_images: list[str] | None = None
    hints: list[str] | None = None
    topic_title: str | None = None
    task_number: int | None = None
    retrievability: float | None = None
    prototype_code: str | None = None
    prototype_title: str | None = None


class FSRSReviewRequest(BaseModel):
    card_id: str
    rating: int = Field(..., ge=1, le=4)
    answer: str = Field("", max_length=50)
    time_spent_seconds: int = Field(0, ge=0, le=36000)


class FSRSReviewResponse(BaseModel):
    is_correct: bool
    correct_answer: str | None = None
    solution_markdown: str | None = None
    xp_earned: int
    new_level_reached: int | None = None
    new_due: str
    new_difficulty: float
    new_stability: float
    new_state: str
    retrievability: float | None = None


class FSRSSessionResponse(BaseModel):
    cards: list[FSRSCardResponse]
    total_due: int

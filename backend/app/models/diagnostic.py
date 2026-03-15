from pydantic import BaseModel, Field


class DiagnosticProblem(BaseModel):
    """A single problem in the diagnostic test."""

    problem_id: str
    task_number: int
    problem_text: str
    problem_images: list[str] | None = None


class DiagnosticStartResponse(BaseModel):
    problems: list[DiagnosticProblem]
    total: int


class DiagnosticAnswer(BaseModel):
    task_number: int = Field(..., ge=1, le=19)
    answer: str | None = None
    self_assessment: str | None = None
    time_spent_seconds: int = Field(..., ge=0, le=36000)


class DiagnosticSubmitRequest(BaseModel):
    answers: list[DiagnosticAnswer] = Field(..., min_length=19, max_length=19)


class DiagnosticResultItem(BaseModel):
    task_number: int
    is_correct: bool | None = None
    self_assessment: str | None = None
    time_spent_seconds: int


class DiagnosticResultResponse(BaseModel):
    results: list[DiagnosticResultItem]
    total_correct: int
    total_answered: int

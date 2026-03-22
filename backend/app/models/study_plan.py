from pydantic import BaseModel, Field, model_validator


class StudyPlanGenerateRequest(BaseModel):
    target_score: int = Field(..., ge=70, le=100)

    @model_validator(mode="after")
    def validate_target_score(self) -> "StudyPlanGenerateRequest":
        if self.target_score not in (70, 80, 90, 100):
            msg = "target_score must be one of: 70, 80, 90, 100"
            raise ValueError(msg)
        return self


class StudyPlanResponse(BaseModel):
    id: str
    user_id: str
    target_score: int
    plan_data: dict | None = None
    generated_at: str
    is_active: bool


class AssessmentAnswer(BaseModel):
    problem_id: str
    answer: str


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswer]


class AssessmentStartResponse(BaseModel):
    task_number: int
    problems: list[dict]


class AssessmentResultResponse(BaseModel):
    task_number: int
    correct_count: int
    total_count: int
    status: str
    details: list[dict]

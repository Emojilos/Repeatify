from pydantic import BaseModel, Field, model_validator


class StudyPlanGenerateRequest(BaseModel):
    target_score: int = Field(..., ge=70, le=100)
    exam_date: str
    hours_per_day: float = Field(..., gt=0, le=10.0)

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
    exam_date: str
    hours_per_day: float
    plan_data: dict | None = None
    generated_at: str
    is_active: bool


class DailyTask(BaseModel):
    task_type: str
    task_number: int | None = None
    prototype_id: str | None = None
    title: str
    estimated_minutes: int | None = None


class DailyTasksResponse(BaseModel):
    review_cards_due: int
    new_material: list[DailyTask]
    total_estimated_minutes: int | None = None

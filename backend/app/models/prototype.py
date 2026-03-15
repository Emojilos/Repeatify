from pydantic import BaseModel


class PrototypeBase(BaseModel):
    task_number: int
    prototype_code: str
    title: str
    description: str | None = None
    difficulty_within_task: str
    estimated_study_minutes: int | None = None


class PrototypeResponse(BaseModel):
    id: str
    task_number: int
    prototype_code: str
    title: str
    description: str | None = None
    difficulty_within_task: str
    estimated_study_minutes: int | None = None
    theory_markdown: str | None = None
    key_formulas: list[dict] | None = None
    solution_algorithm: list[dict] | None = None
    common_mistakes: list[dict] | None = None
    related_prototypes: list[dict] | None = None
    order_index: int | None = None


class PrototypeListItem(BaseModel):
    id: str
    task_number: int
    prototype_code: str
    title: str
    description: str | None = None
    difficulty_within_task: str
    estimated_study_minutes: int | None = None
    order_index: int | None = None


class PrototypeListResponse(BaseModel):
    items: list[PrototypeListItem]
    total: int

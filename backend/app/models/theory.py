from pydantic import BaseModel


class TheoryContentItem(BaseModel):
    id: str
    topic_id: str
    content_type: str  # framework / inquiry / relationships / elaboration / summary
    content_markdown: str
    visual_assets: list = []
    order_index: int = 0


class TheoryResponse(BaseModel):
    topic_id: str
    topic_title: str
    items: list[TheoryContentItem]
    fire_progress: "FireProgress | None" = None


class FireProgress(BaseModel):
    fire_framework_completed: bool = False
    fire_inquiry_completed: bool = False
    fire_relationships_completed: bool = False
    fire_elaboration_completed: bool = False
    fire_completed_at: str | None = None


class FireProgressRequest(BaseModel):
    stage: str  # framework / inquiry / relationships / elaboration


class FireProgressResponse(BaseModel):
    stage: str
    completed: bool
    fire_completed_at: str | None = None
    all_stages_completed: bool = False
    xp_earned: int = 0
    new_level_reached: int | None = None

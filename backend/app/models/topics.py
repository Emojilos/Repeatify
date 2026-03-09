from pydantic import BaseModel


class TopicProgress(BaseModel):
    strength_score: float = 0.0
    fire_completed: bool = False
    fire_completed_at: str | None = None
    total_attempts: int = 0
    correct_attempts: int = 0
    last_practiced_at: str | None = None


class TopicListItem(BaseModel):
    id: str
    task_number: int
    title: str
    description: str | None = None
    difficulty_level: str
    max_points: int
    estimated_study_hours: float | None = None
    order_index: int = 0
    user_progress: TopicProgress | None = None


class TopicDetail(TopicListItem):
    parent_topic_id: str | None = None


class TopicRelationship(BaseModel):
    id: str
    source_topic_id: str
    target_topic_id: str
    relationship_type: str
    description: str | None = None
    related_topic: TopicListItem | None = None

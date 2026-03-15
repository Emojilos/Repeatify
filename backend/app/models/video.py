from pydantic import BaseModel


class VideoResourceResponse(BaseModel):
    id: str
    prototype_id: str
    youtube_video_id: str
    title: str
    channel_name: str | None = None
    duration_seconds: int | None = None
    timestamps: list[dict] | None = None
    order_index: int | None = None

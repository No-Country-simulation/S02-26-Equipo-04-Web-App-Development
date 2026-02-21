from datetime import datetime
from uuid import UUID
from app.schemas.base import BaseSchema


class VideoUploadResponse(BaseSchema):
    video_id: UUID
    bucket: str
    object_key: str
    filename: str
    content_type: str | None
    size_bytes: int
    user_id: UUID | None
    storage_path: str
    uploaded_at: datetime


class VideoURLResponse(BaseSchema):
    video_id: UUID
    url: str
    expires_in_seconds: int
    filename: str


class UserVideoItem(BaseSchema):
    video_id: UUID
    filename: str
    status: str | None = None
    uploaded_at: datetime
    preview_url: str | None = None


class UserVideosResponse(BaseSchema):
    total: int
    limit: int
    offset: int
    videos: list[UserVideoItem]

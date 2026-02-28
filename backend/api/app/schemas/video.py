from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.base import BaseSchema


class VideoFromJobResponse(BaseSchema):
    video_id: UUID
    bucket: str
    object_key: str
    filename: str
    user_id: UUID | None
    storage_path: str
    uploaded_at: datetime

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


class UserVideoDetailResponse(BaseSchema):
    video_id: UUID
    filename: str
    status: str | None = None
    uploaded_at: datetime
    updated_at: datetime
    storage_path: str | None = None
    preview_url: str | None = None


class UpdateVideoRequest(BaseSchema):
    filename: str = Field(min_length=1, max_length=255)


class UserVideosResponse(BaseSchema):
    total: int
    limit: int
    offset: int
    videos: list[UserVideoItem]

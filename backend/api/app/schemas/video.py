from datetime import datetime
from uuid import UUID
from pydantic import Field
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


class ClientVideoMetadata(BaseSchema):
    duration_seconds: int | None = Field(default=None, ge=1, le=86400)
    width: int | None = Field(default=None, ge=1, le=16384)
    height: int | None = Field(default=None, ge=1, le=16384)
    fps: int | None = Field(default=None, ge=1, le=240)


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

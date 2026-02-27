"""Schemas para publicación de videos en YouTube."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema


class YouTubePublishRequest(BaseSchema):
    """Request body para publicar un clip procesado en YouTube."""

    title: str | None = Field(
        default=None,
        max_length=100,
        description="Título del video en YouTube (máx. 100 caracteres)",
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
        description="Descripción del video en YouTube (máx. 5000 caracteres)",
    )
    privacy: str = Field(
        default="private",
        pattern="^(public|private|unlisted)$",
        description="Privacidad: public, private o unlisted",
    )


class YouTubePublishResponse(BaseSchema):
    """Respuesta tras publicar exitosamente un clip en YouTube."""

    success: bool
    message: str
    job_id: UUID
    youtube_video_id: str
    youtube_url: str
    title: str
    privacy: str
    thumbnail_url: str | None = None


class YouTubeConnectionStatus(BaseSchema):
    """Estado de la conexión de YouTube del usuario."""

    connected: bool
    message: str | None = None
    provider_username: str | None = None
    provider_user_id: str | None = None
    token_expires_at: str | None = None
    is_expired: bool | None = None

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class ProfileBase(BaseSchema):
    """Schema base para Profile"""

    display_name: str | None = Field(None, max_length=100, description="Nombre público visible")
    full_name: str | None = Field(None, max_length=200, description="Nombre completo legal")
    birth_date: date | None = Field(None, description="Fecha de nacimiento")
    bio: str | None = Field(None, max_length=500, description="Biografía o descripción personal")
    avatar_url: str | None = Field(None, max_length=500, description="URL de la imagen de perfil")
    preferred_language: str = Field(
        default="es", max_length=10, description="Código de idioma (es, en, etc)"
    )
    timezone: str = Field(default="UTC", max_length=50, description="Zona horaria del usuario")


class ProfileCreate(ProfileBase):
    """
    Schema para crear un profile.

    Normalmente se crea vacío automáticamente al registrar un usuario.
    """

    pass


class ProfileUpdate(BaseSchema):
    """
    Schema para actualizar el profile del usuario.

    Todos los campos son opcionales.
    """

    display_name: str | None = Field(None, max_length=100)
    full_name: str | None = Field(None, max_length=200)
    birth_date: date | None = None
    bio: str | None = Field(None, max_length=500)
    avatar_url: str | None = Field(None, max_length=500)
    preferred_language: str | None = Field(None, max_length=10)
    timezone: str | None = Field(None, max_length=50)

    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        """Valida que el código de idioma sea válido"""
        if v is None:
            return v
        valid_languages = ["es", "en", "pt", "fr", "de", "it"]
        if v not in valid_languages:
            raise ValueError(f"Language must be one of: {', '.join(valid_languages)}")
        return v


class ProfileInDB(ProfileBase):
    """Schema completo del profile en la base de datos"""

    user_id: UUID
    created_at: datetime
    updated_at: datetime


class ProfilePublic(ProfileBase):
    """
    Schema público del profile (para respuestas API).

    Incluye toda la información del perfil del usuario.
    """

    user_id: UUID
    created_at: datetime
    updated_at: datetime

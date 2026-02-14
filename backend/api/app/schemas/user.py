from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, SecretStr, field_validator

from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """Schema base para User (solo email)"""

    email: EmailStr


class UserCreate(UserBase):
    """
    Schema para registro de usuario.

    Solo requiere email y password.
    El Profile se crea vacío automáticamente.
    """

    password: SecretStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseSchema):
    """Schema para actualizar usuario (solo campos de auth)"""

    email: EmailStr | None = None
    password: SecretStr | None = None


class UserInDB(UserBase):
    """Schema completo del usuario en la base de datos"""

    id: UUID
    role: UserRole
    is_active: bool
    is_banned: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserPublic(UserBase):
    """
    Schema público del usuario (para respuestas API).

    Solo devuelve información de autenticación y permisos.
    Para datos personales, usar /profiles/me
    """

    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool

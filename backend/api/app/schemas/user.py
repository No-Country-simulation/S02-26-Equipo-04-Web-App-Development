from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, SecretStr, field_validator
from app.schemas.base import BaseSchema

class UserBase(BaseSchema):
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    password: SecretStr
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: SecretStr) -> SecretStr:
        password = v.get_secret_value()
        if len(password) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in password):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValueError('Password must contain at least one number')
        return v

class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    full_name: str | None = None
    password: SecretStr | None = None

class UserInDB(UserBase):
    id: UUID
    is_active: bool
    is_superuser: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

class UserPublic(UserBase):
    id: UUID
    is_active: bool

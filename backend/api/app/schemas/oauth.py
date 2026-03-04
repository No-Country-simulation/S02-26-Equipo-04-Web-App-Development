"""Schemas para Google OAuth y Facebook OAuth"""
from pydantic import BaseModel, HttpUrl
from typing import Optional


class GoogleAuthURL(BaseModel):
    """URL de autorización de Google + state token"""
    authorization_url: HttpUrl
    state: str


class GoogleUserInfo(BaseModel):
    """Información del usuario obtenida de Google"""
    id: str
    email: str
    verified_email: bool
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None


class GoogleCallbackRequest(BaseModel):
    """Request del frontend con el authorization code"""
    code: str
    state: str


# === FACEBOOK OAUTH ===

class FacebookAuthURL(BaseModel):
    """URL de autorización de Facebook + state token para CSRF protection"""
    authorization_url: str
    state: str


class FacebookUserInfo(BaseModel):
    """Información del usuario obtenida desde Facebook Graph API"""
    id: str
    name: Optional[str] = None
    email: Optional[str] = None       # Puede ser None si el usuario lo rechaza
    picture_url: Optional[str] = None  # URL de foto de perfil


class FacebookCallbackRequest(BaseModel):
    """Request del frontend con el authorization code de Facebook"""
    code: str
    state: str

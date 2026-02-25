"""Schemas para OAuth (Google, Instagram)"""
from pydantic import BaseModel, HttpUrl


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


# === INSTAGRAM OAUTH ===

class InstagramAuthURL(BaseModel):
    """URL de autorización de Instagram + state token"""
    authorization_url: HttpUrl
    state: str


class InstagramCallbackRequest(BaseModel):
    """Request del frontend con el authorization code de Instagram"""
    code: str
    state: str

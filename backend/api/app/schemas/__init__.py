"""
Schemas de la aplicación (Pydantic).

Usados para validación de entrada/salida de la API.
"""
from app.schemas.user import UserCreate, UserUpdate, UserPublic, UserInDB
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfilePublic, ProfileInDB
from app.schemas.token import Token, TokenPayload
from app.schemas.response import APIException, ErrorResponse, ErrorDetail
from app.schemas.oauth import GoogleAuthURL, GoogleUserInfo, GoogleCallbackRequest
from app.schemas.youtube import YouTubePublishRequest, YouTubePublishResponse, YouTubeConnectionStatus

__all__ = [
    "UserCreate",
    "UserUpdate", 
    "UserPublic",
    "UserInDB",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfilePublic",
    "ProfileInDB",
    "Token",
    "TokenPayload",
    "APIException",
    "ErrorResponse",
    "ErrorDetail",
    "GoogleAuthURL",
    "GoogleUserInfo",
    "GoogleCallbackRequest",
    "YouTubePublishRequest",
    "YouTubePublishResponse",
    "YouTubeConnectionStatus",
]
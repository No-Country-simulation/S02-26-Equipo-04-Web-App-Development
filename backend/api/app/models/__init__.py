"""
Modelos de la aplicación.

Importados aquí para que Alembic los detecte automáticamente.
"""
from app.models.user import User
from app.models.profile import Profile
from app.models.oauth_token import OAuthToken
from app.models.enums import UserRole
from app.models.video import Video
from app.models.job import Job
from app.models.audio import Audio

__all__ = [
    "User",
    "Profile",
    "OAuthToken",
    "UserRole",
    "UserRole",
    "Video",
    "Job",
    "Audio"
]
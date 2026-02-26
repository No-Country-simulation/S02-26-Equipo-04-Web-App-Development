"""
Modelos de la aplicación.

Importados aquí para que Alembic los detecte automáticamente.
"""
from app.models.user import User
from app.models.profile import Profile
from app.models.oauth_token import OAuthToken
from app.models.enums import UserRole

__all__ = ["User", "Profile", "OAuthToken", "UserRole"]
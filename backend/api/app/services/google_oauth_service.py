"""Servicio de autenticación con Google OAuth 2.0"""

import secrets
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
import httpx

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.profile import Profile
from app.models.enums import UserRole
from app.schemas.oauth import GoogleAuthURL, GoogleUserInfo

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Servicio para manejar el flujo completo de Google OAuth"""

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    SCOPES = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]

    def __init__(self, db: Session):
        self.db = db

    def get_authorization_url(self) -> GoogleAuthURL:
        """
        Genera la URL de autorización de Google + state token para CSRF protection.

        Returns:
            GoogleAuthURL: URL donde redirigir al usuario + state token
        """
        # Generar state token aleatorio para CSRF protection
        state = secrets.token_urlsafe(32)

        # Construir URL de autorización
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "state": state,
            "access_type": "offline",  # Para refresh token
            "prompt": "select_account",  # Forzar selección de cuenta
        }

        # Construir query string manualmente
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        authorization_url = f"{self.GOOGLE_AUTH_URL}?{query_string}"

        return GoogleAuthURL(authorization_url=authorization_url, state=state)

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Intercambia el authorization code por un access token.

        Este paso se hace server-to-server, el client_secret NUNCA se expone al frontend.

        Args:
            code: Authorization code recibido de Google

        Returns:
            Dict con access_token, refresh_token, etc.
        """
        # Log para debugging (sin exponer client_secret completo)
        logger.debug(f"🔐 Intercambiando código por token...")
        logger.debug(f"📍 Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
        logger.debug(f"🔑 Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")
        logger.debug(f"📝 Code length: {len(code)} chars")

        async with httpx.AsyncClient() as client:
            token_data = {
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            response = await client.post(self.GOOGLE_TOKEN_URL, data=token_data)

            # Si hay error, loguear respuesta de Google
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"❌ Google OAuth error: {response.status_code}")
                logger.error(f"📄 Response: {error_detail}")

            response.raise_for_status()
            return response.json()

    async def get_user_info(self, access_token: str) -> GoogleUserInfo:
        """
        Obtiene la información del usuario desde Google.

        Args:
            access_token: Token de acceso obtenido en el paso anterior

        Returns:
            GoogleUserInfo: Datos del usuario (email, nombre, foto, etc.)
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            data = response.json()

            return GoogleUserInfo(**data)

    def get_or_create_user(self, google_user: GoogleUserInfo) -> User:
        """
        Busca o crea un usuario basado en la info de Google.

        Args:
            google_user: Información del usuario desde Google

        Returns:
            User: Usuario creado o encontrado
        """
        # Buscar usuario existente por email
        user = self.db.query(User).filter(User.email == google_user.email).first()

        if user:
            # Usuario existe - actualizar provider si era de email
            if user.provider == "email":
                user.provider = "google"
                user.provider_user_id = google_user.id
                user.is_verified = True  # Google ya verificó el email
                self.db.commit()
                self.db.refresh(user)
            return user

        # Usuario NO existe - crear nuevo
        new_user = User(
            email=google_user.email,
            provider="google",
            provider_user_id=google_user.id,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,  # Google ya verificó el email
            hashed_password=None,  # No tiene password (OAuth)
        )
        self.db.add(new_user)
        self.db.flush()  # Generar el ID sin hacer commit

        # Crear perfil automático con datos de Google
        profile = Profile(
            user_id=new_user.id,
            full_name=google_user.name,
            display_name=google_user.given_name or google_user.name,
            avatar_url=google_user.picture,
            preferred_language=google_user.locale or "es",
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    async def authenticate_with_google(self, code: str) -> Dict[str, Any]:
        """
        Flujo completo de autenticación con Google.

        1. Intercambia code por access_token
        2. Obtiene info del usuario
        3. Crea/actualiza usuario en DB
        4. Genera JWT propio

        Args:
            code: Authorization code desde Google

        Returns:
            Dict con access_token (JWT propio) y datos del usuario
        """
        # 1. Intercambiar code por token
        token_data = await self.exchange_code_for_token(code)
        access_token = token_data["access_token"]

        # 2. Obtener info del usuario
        google_user = await self.get_user_info(access_token)

        # 3. Crear/actualizar usuario en DB
        user = self.get_or_create_user(google_user)

        # 4. Generar nuestro propio JWT
        jwt_token = create_access_token(subject=str(user.id))

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES
            * 60,  # Convertir a segundos
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
        }

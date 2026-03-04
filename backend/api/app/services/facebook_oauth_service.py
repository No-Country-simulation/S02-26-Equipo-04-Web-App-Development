"""Servicio de autenticacion con Facebook OAuth 2.0."""

import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import httpx

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.profile import Profile
from app.models.oauth_token import OAuthToken
from app.models.enums import UserRole
from app.schemas.oauth import FacebookAuthURL, FacebookUserInfo
from app.utils.redis_client import redis_client

logger = logging.getLogger(__name__)

PROVIDER = "facebook"
STATE_TTL_SECONDS = 600  # 10 minutos
HTTPX_TIMEOUT = 10.0     # segundos


class FacebookOAuthService:
    """Servicio para manejar el flujo completo de Facebook OAuth 2.0.

    Diferencias clave respecto a Google OAuth:
    - El intercambio de token usa GET, no POST.
    - Los scopes se separan con comas, no con espacios.
    - La informacion del usuario requiere el parametro fields.
    - La foto de perfil viene anidada en picture.data.url.
    - No existe refresh_token; los tokens son long-lived (~60 dias).
    - El email puede ser None si el usuario rechaza compartirlo.
    """

    FACEBOOK_AUTH_URL = "https://www.facebook.com/v22.0/dialog/oauth"
    FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v22.0/oauth/access_token"
    FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"
    SCOPES = ["public_profile", "email"]

    def __init__(self, db: Session):
        """
        Args:
            db: Sesion de base de datos SQLAlchemy.
        """
        self.db = db

    def get_authorization_url(self) -> FacebookAuthURL:
        """Genera la URL de autorizacion de Facebook con state token para CSRF protection.

        El state se persiste en Redis con TTL de 10 minutos.
        Debe validarse en el callback antes de procesar el code.

        Returns:
            FacebookAuthURL: URL de autorizacion y state token.
        """
        state = secrets.token_urlsafe(32)

        redis_key = f"oauth:facebook:state:{state}"
        redis_client.client.setex(redis_key, STATE_TTL_SECONDS, "1")
        logger.debug("Facebook OAuth state stored in Redis: key=%s ttl=%ds", redis_key, STATE_TTL_SECONDS)

        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
            "response_type": "code",
            "scope": ",".join(self.SCOPES),
            "state": state,
        }

        authorization_url = f"{self.FACEBOOK_AUTH_URL}?{urlencode(params)}"

        logger.info("Facebook OAuth authorization URL generated")
        logger.debug("redirect_uri=%s", settings.FACEBOOK_REDIRECT_URI)

        return FacebookAuthURL(authorization_url=authorization_url, state=state)

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Intercambia el authorization code por un access token de Facebook.

        Usa GET con query params, a diferencia de Google que usa POST con body.

        Args:
            code: Authorization code recibido de Facebook. Debe estar limpio
                  (sin `&state=...` ni `#_=_` al final).

        Returns:
            Dict con access_token, token_type y expires_in.

        Raises:
            httpx.HTTPStatusError: Si Facebook retorna un error HTTP.
            ValueError: Si la respuesta no contiene access_token.
        """
        logger.debug("Exchanging Facebook authorization code for token (length=%d)", len(code))

        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            params = {
                "client_id": settings.FACEBOOK_APP_ID,
                "client_secret": settings.FACEBOOK_APP_SECRET,
                "redirect_uri": settings.FACEBOOK_REDIRECT_URI,
                "code": code,
            }

            response = await client.get(self.FACEBOOK_TOKEN_URL, params=params)

            if response.status_code != 200:
                logger.error(
                    "Facebook token exchange failed: status=%s body=%s",
                    response.status_code,
                    response.text,
                )

            response.raise_for_status()
            data = response.json()

        if "access_token" not in data:
            logger.error("Facebook token response missing access_token: %s", data)
            raise ValueError("Facebook token response did not contain access_token")

        return data

    async def get_user_info(self, access_token: str) -> FacebookUserInfo:
        """Obtiene la informacion del usuario desde Facebook Graph API.

        El parametro fields es obligatorio; sin el Facebook no devuelve email ni picture.
        La foto de perfil viene anidada en picture.data.url.

        Args:
            access_token: Token de acceso de Facebook.

        Returns:
            FacebookUserInfo: Datos del usuario.

        Raises:
            httpx.HTTPStatusError: Si la Graph API retorna un error HTTP.
        """
        async with httpx.AsyncClient(timeout=HTTPX_TIMEOUT) as client:
            params = {
                "fields": "id,name,email,picture.width(200).height(200)",
                "access_token": access_token,
            }

            response = await client.get(self.FACEBOOK_USERINFO_URL, params=params)
            response.raise_for_status()
            data = response.json()

        picture_url: Optional[str] = None
        picture_data = data.get("picture", {}).get("data", {})
        if picture_data:
            picture_url = picture_data.get("url")

        logger.info("Facebook user info retrieved: facebook_id=%s", data.get("id"))

        return FacebookUserInfo(
            id=data["id"],
            name=data.get("name"),
            email=data.get("email"),
            picture_url=picture_url,
        )

    def get_or_create_user(self, facebook_user: FacebookUserInfo) -> User:
        """Busca o crea un usuario a partir de la informacion de Facebook.

        Casos manejados:
        - Usuario nuevo: crea User y Profile dentro de la misma transaccion.
        - Usuario existente con mismo email y distinto provider: vincula a Facebook.
        - Facebook no provee email: usa {facebook_id}@facebook.placeholder.
        - Race condition: captura IntegrityError y reintenta la query.

        Usa flush() sin commit(). La transaccion la controla authenticate_with_facebook.

        Args:
            facebook_user: Informacion del usuario obtenida desde Facebook.

        Returns:
            User: Usuario creado o encontrado.
        """
        if facebook_user.email:
            email = facebook_user.email
        else:
            email = f"{facebook_user.id}@{PROVIDER}.placeholder"
            logger.warning(
                "Facebook did not provide email for facebook_id=%s, using placeholder",
                facebook_user.id,
            )

        user = self.db.query(User).filter(User.email == email).first()

        if user:
            if user.provider != PROVIDER:
                user.provider = PROVIDER
                user.provider_user_id = facebook_user.id
                user.is_verified = True
                self.db.flush()
                logger.info("Existing user linked to Facebook: user_id=%s", user.id)
            return user

        try:
            new_user = User(
                email=email,
                provider=PROVIDER,
                provider_user_id=facebook_user.id,
                role=UserRole.USER,
                is_active=True,
                is_verified=True,
                hashed_password=None,
            )
            self.db.add(new_user)
            self.db.flush()

            profile = Profile(
                user_id=new_user.id,
                full_name=facebook_user.name,
                display_name=facebook_user.name,
                avatar_url=facebook_user.picture_url,
                preferred_language="es",
            )
            self.db.add(profile)
            self.db.flush()

            logger.info("New user created from Facebook: user_id=%s", new_user.id)
            return new_user

        except IntegrityError:
            self.db.rollback()
            logger.warning(
                "IntegrityError creating Facebook user (race condition), retrying query: email=%s",
                email,
            )
            user = self.db.query(User).filter(User.email == email).first()
            if user is None:
                raise
            return user

    async def authenticate_with_facebook(self, code: str, state: str) -> Dict[str, Any]:
        """Ejecuta el flujo completo de autenticacion con Facebook.

        Valida el state contra Redis para prevenir ataques CSRF.
        Todos los cambios en DB se persisten en un unico commit al final
        para garantizar atomicidad. Si cualquier paso falla, se hace rollback
        y ningun cambio queda persistido.

        Pasos:
        1. Valida state contra Redis y lo elimina (one-time use).
        2. Intercambia el code por un access_token de Facebook.
        3. Obtiene los datos del usuario desde Graph API.
        4. Crea o actualiza el usuario en la base de datos (flush).
        5. Persiste el token OAuth de Facebook (flush).
        6. Hace commit unico de toda la transaccion.
        7. Genera y retorna un JWT propio de la aplicacion.

        Args:
            code: Authorization code limpio recibido de Facebook.
            state: State token para validacion CSRF.

        Returns:
            Dict con access_token (JWT), token_type, expires_in y datos del usuario.

        Raises:
            ValueError: Si el state es invalido o ha expirado.
            httpx.HTTPStatusError: Si falla la comunicacion con Facebook.
            sqlalchemy.exc.SQLAlchemyError: Si falla la persistencia en DB.
        """
        redis_key = f"oauth:facebook:state:{state}"
        stored = redis_client.client.getdel(redis_key)
        if stored is None:
            logger.warning("Facebook OAuth state validation failed: state=%s", state)
            raise ValueError("Invalid or expired OAuth state. Please restart the login flow.")

        token_data = await self.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 5_184_000)

        facebook_user = await self.get_user_info(access_token)
        user = self.get_or_create_user(facebook_user)

        self._save_or_update_oauth_token(
            user_id=user.id,
            access_token=access_token,
            expires_in=expires_in,
            token_type=token_data.get("token_type", "bearer"),
            provider_user_id=facebook_user.id,
        )

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        jwt_token = create_access_token(subject=str(user.id))
        logger.info("Facebook authentication successful: user_id=%s", user.id)

        return {
            "access_token": jwt_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
            },
        }

    def _save_or_update_oauth_token(
        self,
        user_id: str,
        access_token: str,
        expires_in: int,
        token_type: str,
        provider_user_id: str,
    ) -> None:
        """Persiste o actualiza el token OAuth de Facebook sin hacer commit.

        Facebook no emite refresh_token; los tokens son long-lived (~60 dias).
        El commit es responsabilidad exclusiva de authenticate_with_facebook.

        Args:
            user_id: ID del usuario en la base de datos.
            access_token: Token de acceso de Facebook.
            expires_in: Tiempo de expiracion en segundos.
            token_type: Tipo de token (generalmente 'bearer').
            provider_user_id: ID del usuario en Facebook.
        """
        existing_token = (
            self.db.query(OAuthToken)
            .filter(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == PROVIDER,
            )
            .first()
        )

        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=expires_in)

        if existing_token:
            existing_token.access_token = access_token
            existing_token.expires_at = expires_at
            existing_token.token_type = token_type
            existing_token.provider_user_id = provider_user_id
            existing_token.last_refreshed_at = now
            logger.debug("Facebook OAuth token updated: user_id=%s", user_id)
        else:
            new_token = OAuthToken(
                user_id=user_id,
                provider=PROVIDER,
                access_token=access_token,
                refresh_token=None,
                token_type=token_type,
                scope=",".join(self.SCOPES),
                expires_at=expires_at,
                provider_user_id=provider_user_id,
            )
            self.db.add(new_token)
            logger.debug("Facebook OAuth token created: user_id=%s", user_id)



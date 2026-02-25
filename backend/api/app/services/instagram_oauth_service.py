"""Servicio para autenticación OAuth 2.0 con Instagram Business Login"""
import logging
import secrets
from typing import Dict
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.oauth import InstagramAuthURL
from app.schemas.token import Token
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class InstagramOAuthService:
    """Servicio para manejar el flujo OAuth de Instagram"""
    
    # Instagram OAuth URLs
    INSTAGRAM_AUTH_URL = "https://api.instagram.com/oauth/authorize"
    INSTAGRAM_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
    INSTAGRAM_USER_URL = "https://graph.instagram.com/me"
    
    # Scopes necesarios
    SCOPES = [
        "instagram_business_basic",  # Perfil básico
        "instagram_business_content_publish"  # Publicar contenido
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_authorization_url(self) -> InstagramAuthURL:
        """
        Genera la URL de autorización de Instagram.
        
        Returns:
            InstagramAuthURL con la URL y el state token para CSRF protection
        """
        state = secrets.token_urlsafe(32)
        
        # Construir URL de autorización
        params = {
            "client_id": settings.INSTAGRAM_APP_ID,
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "scope": ",".join(self.SCOPES),
            "response_type": "code",
            "state": state
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{self.INSTAGRAM_AUTH_URL}?{query_string}"
        
        logger.info(f"Instagram OAuth URL generada con state: {state[:10]}...")
        
        return InstagramAuthURL(
            authorization_url=authorization_url,
            state=state
        )
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """
        Intercambia el código de autorización por un access token.
        
        Args:
            code: Código de autorización de Instagram
            
        Returns:
            Dict con access_token y user_id
            
        Raises:
            HTTPException si falla el intercambio
        """
        data = {
            "client_id": settings.INSTAGRAM_APP_ID,
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
            "code": code
        }
        
        logger.info(f"Intercambiando código Instagram (length: {len(code)})")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.INSTAGRAM_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Error en token exchange: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error intercambiando código: {response.text}"
                    )
                
                token_data = response.json()
                logger.info(f"Token obtenido para user_id: {token_data.get('user_id')}")
                return token_data
                
            except httpx.RequestError as e:
                logger.error(f"Error de red en token exchange: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Error de conexión con Instagram"
                )
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Obtiene información del usuario desde Instagram Graph API.
        
        Args:
            access_token: Token de acceso de Instagram
            
        Returns:
            Dict con id, username, account_type
        """
        params = {
            "fields": "id,username,account_type",
            "access_token": access_token
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.INSTAGRAM_USER_URL,
                    params=params
                )
                
                if response.status_code != 200:
                    logger.error(f"Error obteniendo user info: {response.text}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Error obteniendo información del usuario"
                    )
                
                user_info = response.json()
                logger.info(f"User info obtenido: {user_info.get('username')}")
                return user_info
                
            except httpx.RequestError as e:
                logger.error(f"Error de red obteniendo user info: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Error de conexión con Instagram"
                )
    
    def get_or_create_user(self, instagram_user: Dict, access_token: str) -> User:
        """
        Busca o crea un usuario basado en los datos de Instagram.
        
        Args:
            instagram_user: Datos del usuario de Instagram
            access_token: Token de acceso de Instagram (para guardar)
            
        Returns:
            User object
        """
        instagram_user_id = instagram_user["id"]
        username = instagram_user.get("username", "instagram_user")
        
        # Buscar usuario existente por provider_user_id
        user = self.db.query(User).filter(
            User.provider == "instagram",
            User.provider_user_id == instagram_user_id
        ).first()
        
        if user:
            # Actualizar last_login_at
            user.last_login_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Usuario Instagram existente: {username}")
            return user
        
        # Crear nuevo usuario
        new_user = User(
            email=f"{instagram_user_id}@instagram.oauth",  # Email placeholder
            provider="instagram",
            provider_user_id=instagram_user_id,
            role=UserRole.USER,
            is_active=True,
            is_verified=True,  # Instagram ya verificó la identidad
            last_login_at=datetime.utcnow()
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        logger.info(f"Nuevo usuario Instagram creado: {username} (ID: {new_user.id})")
        return new_user
    
    async def authenticate_with_instagram(self, code: str) -> Token:
        """
        Flujo completo de autenticación con Instagram.
        
        Args:
            code: Código de autorización de Instagram
            
        Returns:
            Token JWT propio + datos del usuario
        """
        # 1. Intercambiar código por token
        token_data = await self.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        
        # 2. Obtener info del usuario
        instagram_user = await self.get_user_info(access_token)
        
        # 3. Crear/actualizar usuario en DB
        user = self.get_or_create_user(instagram_user, access_token)
        
        # 4. Generar JWT propio
        jwt_token = create_access_token(subject=str(user.id))
        
        return Token(
            access_token=jwt_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

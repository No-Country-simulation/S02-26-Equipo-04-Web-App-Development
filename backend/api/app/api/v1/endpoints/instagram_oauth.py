"""Endpoints para Instagram OAuth 2.0"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.instagram_oauth_service import InstagramOAuthService
from app.schemas.oauth import InstagramAuthURL, InstagramCallbackRequest
from app.schemas.token import Token

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/instagram/login", response_model=InstagramAuthURL)
def instagram_login(db: Session = Depends(get_db)):
    """
    Genera la URL de autorización de Instagram.
    
    El frontend debe:
    1. Guardar el state en sessionStorage
    2. Redirigir al usuario a authorization_url
    3. Instagram redirigirá de vuelta con un code
    
    Returns:
        InstagramAuthURL: URL de Instagram + state token para CSRF protection
    """
    oauth_service = InstagramOAuthService(db)
    return oauth_service.get_authorization_url()


@router.post("/instagram/callback", response_model=Token)
async def instagram_callback(
    callback_data: InstagramCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Procesa el callback de Instagram después del login.
    
    El frontend debe:
    1. Validar que el state coincida con el guardado
    2. Enviar el code y state a este endpoint
    3. Guardar el access_token recibido
    
    Args:
        callback_data: code y state desde Instagram
        
    Returns:
        Token: JWT propio + datos del usuario
    """
    oauth_service = InstagramOAuthService(db)
    
    try:
        token = await oauth_service.authenticate_with_instagram(callback_data.code)
        return token
    except Exception as e:
        logger.error(f"Error en Instagram callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en autenticación con Instagram: {str(e)}"
        )

"""Endpoints para Google OAuth 2.0"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.services.google_oauth_service import GoogleOAuthService
from app.schemas.oauth import GoogleAuthURL, GoogleCallbackRequest
from app.schemas.token import Token


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/google/login", response_model=GoogleAuthURL)
def google_login(db: Session = Depends(get_db)):
    """
    Genera la URL de autorización de Google.
    
    El frontend debe:
    1. Guardar el state en sessionStorage
    2. Redirigir al usuario a authorization_url
    3. Google redirigirá de vuelta con un code
    
    Returns:
        GoogleAuthURL: URL de Google + state token para CSRF protection
    """
    oauth_service = GoogleOAuthService(db)
    return oauth_service.get_authorization_url()


@router.post("/google/callback", response_model=Token)
async def google_callback(
    callback_data: GoogleCallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Procesa el callback de Google después del login.
    
    El frontend debe:
    1. Validar que el state coincida con el guardado
    2. Enviar el code y state a este endpoint
    3. Guardar el access_token recibido
    
    Args:
        callback_data: code y state desde Google
        
    Returns:
        Token: JWT propio + datos del usuario
        
    Raises:
        HTTPException 400: Si hay error en el flujo OAuth
    """
    oauth_service = GoogleOAuthService(db)
    
    try:
        # Flujo completo: code → token → user info → DB → JWT
        result = await oauth_service.authenticate_with_google(callback_data.code)
        return result
    except Exception as e:
        logger.error(f"Error en OAuth callback: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error en autenticación con Google: {str(e)}"
        )

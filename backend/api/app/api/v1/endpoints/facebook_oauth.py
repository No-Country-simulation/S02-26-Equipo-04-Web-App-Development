"""Endpoints para Facebook OAuth 2.0."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx

from app.core.dependencies import get_db
from app.services.facebook_oauth_service import FacebookOAuthService
from app.schemas.oauth import FacebookAuthURL, FacebookCallbackRequest
from app.schemas.token import Token

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/facebook/login",
    response_model=FacebookAuthURL,
    summary="Iniciar login con Facebook",
    description="""
    Genera la URL de autorizacion de Facebook para iniciar el flujo OAuth 2.0.

    **Pasos para probar desde Swagger:**
    1. Ejecutar este endpoint y copiar `authorization_url`.
    2. Abrir esa URL en el navegador e iniciar sesion en Facebook.
    3. Facebook redirige a `localhost:8000/api/v1/auth/facebook/callback?code=...`.
    4. Esa pagina muestra el `code` limpio para copiar.
    5. Usar ese `code` en el endpoint `POST /facebook/callback`.
    """,
)
def facebook_login(db: Session = Depends(get_db)) -> FacebookAuthURL:
    """Genera la URL de autorizacion de Facebook.

    Returns:
        FacebookAuthURL: URL de autorizacion y state token para CSRF protection.
    """
    service = FacebookOAuthService(db)
    return service.get_authorization_url()


@router.get(
    "/facebook/callback",
    include_in_schema=False,
)
def facebook_callback_browser(code: str, state: str = ""):
    """
    Recibe el redirect del navegador desde Facebook tras la autorizacion.

    No procesa la autenticacion directamente. Devuelve el code limpio
    para que el desarrollador lo use en el endpoint POST /facebook/callback
    desde Swagger u otro cliente HTTP.
    """
    clean_code = code.split("&")[0].split("#")[0]
    return {
        "code": clean_code,
        "state": state,
        "next_step": "POST /api/v1/auth/facebook/callback con el 'code' de arriba",
    }


@router.post(
    "/facebook/callback",
    response_model=Token,
    summary="Procesar callback de Facebook OAuth",
    description="""
    Completa el flujo OAuth intercambiando el `code` por un JWT de la aplicacion.

    **Flujo interno:**
    1. Valida el `state` contra Redis para prevenir ataques CSRF.
    2. Intercambia el `code` por un access_token de Facebook.
    3. Obtiene datos del usuario desde Graph API (id, name, email, picture).
    4. Crea o actualiza el usuario en la base de datos.
    5. Persiste el token OAuth de Facebook.
    6. Retorna un JWT propio de la aplicacion.
    """,
    responses={
        200: {"description": "Autenticacion exitosa, retorna JWT"},
        400: {"description": "Code invalido, expirado o error de Facebook API"},
        500: {"description": "Error interno del servidor"},
    },
)
async def facebook_callback(
    callback_data: FacebookCallbackRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Procesa el authorization code de Facebook y retorna un JWT.

    Args:
        callback_data: code y state recibidos de Facebook.
        db: Sesion de base de datos.

    Returns:
        Token: JWT de la aplicacion, token_type y datos basicos del usuario.

    Raises:
        HTTPException 400: Si el code es invalido o Facebook rechaza la solicitud.
        HTTPException 500: Si ocurre un error interno inesperado.
    """
    try:
        service = FacebookOAuthService(db)
        return await service.authenticate_with_facebook(callback_data.code, callback_data.state)
    except ValueError as exc:
        logger.warning("Facebook OAuth CSRF validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Facebook API error during callback: status=%s body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Facebook authentication failed. The code may be invalid or expired.",
        )
    except Exception:
        logger.exception("Unexpected error during Facebook callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during Facebook authentication.",
        )


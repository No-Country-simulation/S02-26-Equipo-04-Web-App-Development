from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nuevo usuario",
    description="Crea una nueva cuenta de usuario y devuelve un token de acceso",
    responses={
        201: {"description": "Usuario creado exitosamente"},
        409: {"description": "El email ya está registrado"},
        422: {"description": "Datos de entrada inválidos"},
    },
)
async def register(user_data: UserCreate, db: Annotated[Session, Depends(get_db)]) -> Token:
    """
    Registra un nuevo usuario en el sistema.

    - **email**: Email válido (único en el sistema)
    - **password**: Mínimo 8 caracteres, debe incluir mayúscula, minúscula y número
    - **full_name**: Nombre completo (opcional)

    Retorna un token JWT válido por 30 minutos.
    """
    auth_service = AuthService(db)
    user = auth_service.register_user(user_data)
    token = auth_service.create_token_for_user(user)
    return token


@router.post(
    "/login",
    response_model=Token,
    summary="Iniciar sesión",
    description="Autentica un usuario y devuelve un token de acceso",
    responses={
        200: {"description": "Autenticación exitosa"},
        401: {"description": "Credenciales inválidas"},
        403: {"description": "Usuario inactivo"},
    },
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Autentica un usuario existente.

    - **username**: Email del usuario (OAuth2 usa 'username' pero enviamos email)
    - **password**: Contraseña del usuario

    Retorna un token JWT válido por 30 minutos.
    """
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    token = auth_service.create_token_for_user(user)
    return token


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Obtener perfil actual",
    description="Devuelve la información del usuario autenticado",
    responses={
        200: {"description": "Perfil del usuario"},
        401: {"description": "No autenticado o token inválido"},
        403: {"description": "Usuario inactivo"},
    },
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserPublic:
    """
    Obtiene el perfil del usuario autenticado.

    Requiere token JWT válido en el header:
    `Authorization: Bearer <token>`
    """
    return UserPublic.model_validate(current_user)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión",
    description="Invalida el token actual (placeholder - implementar blacklist con Redis)",
    responses={204: {"description": "Sesión cerrada exitosamente"}},
)
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]) -> None:
    """
    Cierra la sesión del usuario actual.

    TODO: Implementar blacklist de tokens en Redis para invalidación real.
    Por ahora, el cliente debe eliminar el token.
    """
    pass


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refrescar token",
    description="Genera un nuevo token para el usuario autenticado",
    responses={
        200: {"description": "Token renovado exitosamente"},
        401: {"description": "Token inválido o expirado"},
    },
)
async def refresh_token(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Genera un nuevo token JWT para el usuario actual.

    Útil para renovar tokens antes de que expiren.
    """
    auth_service = AuthService(db)
    token = auth_service.create_token_for_user(current_user)
    return token

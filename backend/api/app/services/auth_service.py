from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.profile import Profile
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.utils.exceptions import (
    InvalidCredentialsException,
    InactiveUserException,
    UserAlreadyExistsException
)

class AuthService:
    """Servicio de autenticación - Lógica de negocio pura (sin HTTP)"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str) -> User:
        """
        Autentica un usuario por email/password.
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            
        Returns:
            User si autenticación exitosa
            
        Raises:
            InvalidCredentialsException: Si email no existe o password incorrecto
            InactiveUserException: Si usuario está desactivado
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            raise InvalidCredentialsException()
        
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()
        
        if not user.is_active:
            raise InactiveUserException()
        
        user.last_login_at = datetime.utcnow()
        self.db.commit()
        
        return user
    
    def register_user(self, user_data: UserCreate) -> User:
        """
        Registra un nuevo usuario y crea su profile vacío.
        
        Args:
            user_data: Datos de registro validados por Pydantic (email + password)
            
        Returns:
            User creado (con profile asociado)
            
        Raises:
            UserAlreadyExistsException: Si email ya existe
        """
        # Verificar si el email ya existe
        existing = self.db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise UserAlreadyExistsException()
        
        # Hash del password
        password_hash = get_password_hash(user_data.password.get_secret_value())
        
        # Crear usuario
        user = User(
            email=user_data.email,
            hashed_password=password_hash,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        self.db.flush()  # Genera el user.id sin hacer commit
        
        # Crear profile vacío asociado
        profile = Profile(user_id=user.id)
        self.db.add(profile)
        
        # Commit de ambos
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def create_token_for_user(self, user: User) -> Token:
        """
        Crea un JWT token para el usuario.
        
        Args:
            user: Usuario autenticado
            
        Returns:
            Token con access_token y metadata
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(str(user.id), expires_delta)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(expires_delta.total_seconds())
        )

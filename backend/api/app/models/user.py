from sqlalchemy import Boolean, Column, String, DateTime, Enum
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin
from app.models.enums import UserRole


class User(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    """
    Modelo de usuario para autenticación y autorización.
    
    Contiene únicamente información crítica de auth y permisos.
    Los datos personales están en la tabla Profile (relación 1:1).
    """
    __tablename__ = "users"
    
    # === AUTENTICACIÓN ===
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # === PERMISOS Y ESTADO ===
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # === AUDITORÍA ===
    last_login_at = Column(DateTime, nullable=True)
    # created_at, updated_at → heredados de TimestampMixin
    
    # === RELACIÓN ===
    profile = relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")

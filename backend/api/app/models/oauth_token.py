"""Modelo para almacenar tokens OAuth de servicios externos (YouTube, Instagram, etc.)"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin


class OAuthToken(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    """
    Almacena tokens de acceso OAuth para servicios externos.
    
    Permite a los usuarios conectar sus cuentas de YouTube, Instagram, etc.
    y publicar contenido en su nombre sin volver a autenticarse.
    
    Security Best Practices:
    - access_token y refresh_token deberían encriptarse en producción
    - tokens_expiry debe verificarse antes de cada uso
    - refresh_token se usa para renovar access_token automáticamente
    """
    __tablename__ = "oauth_tokens"
    
    # === RELACIÓN CON USUARIO ===
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # === IDENTIFICACIÓN DEL SERVICIO ===
    provider = Column(String, nullable=False)  # "youtube", "instagram", "tiktok", etc.
    
    # === TOKENS ===
    access_token = Column(Text, nullable=False)  # Token de acceso (corta duración: ~1h)
    refresh_token = Column(Text, nullable=True)  # Token de refresh (larga duración: meses/años)
    token_type = Column(String, default="Bearer", nullable=False)  # Tipo de token (Bearer, etc.)
    
    # === METADATA ===
    scope = Column(Text, nullable=True)  # Permisos otorgados (ej: "youtube.upload youtube.readonly")
    expires_at = Column(DateTime, nullable=True)  # Cuándo expira el access_token
    
    # === INFORMACIÓN ADICIONAL ===
    provider_user_id = Column(String, nullable=True)  # ID del usuario en el servicio externo
    provider_username = Column(String, nullable=True)  # Username en el servicio (para UI)
    
    # === AUDITORÍA ===
    last_refreshed_at = Column(DateTime, nullable=True)  # Última vez que se renovó el token
    # created_at, updated_at → heredados de TimestampMixin
    
    # === RELACIÓN ===
    user = relationship("User", backref="oauth_tokens")
    
    def is_expired(self) -> bool:
        """Verifica si el access_token está expirado"""
        if not self.expires_at:
            return False
        return datetime.utcnow() >= self.expires_at
    
    def __repr__(self):
        return f"<OAuthToken(user_id={self.user_id}, provider={self.provider}, expires_at={self.expires_at})>"

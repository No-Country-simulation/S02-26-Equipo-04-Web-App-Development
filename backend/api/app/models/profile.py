from sqlalchemy import Column, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.models.base import TimestampMixin


class Profile(Base, TimestampMixin):
    """
    Perfil de usuario con datos personales y preferencias.

    Relación 1:1 con User. Se crea automáticamente al registrar un usuario.
    Contiene información mutable que el usuario puede editar.
    """

    __tablename__ = "profiles"

    # === CLAVE PRIMARIA Y FORÁNEA ===
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # === IDENTIDAD ===
    display_name = Column(String(100), nullable=True, comment="Nombre público visible")
    full_name = Column(String(200), nullable=True, comment="Nombre completo legal")
    birth_date = Column(Date, nullable=True)

    # === CONTENIDO ===
    bio = Column(Text, nullable=True, comment="Biografía o descripción personal")
    avatar_url = Column(String(500), nullable=True, comment="URL de la imagen de perfil")

    # === PREFERENCIAS ===
    preferred_language = Column(
        String(10), default="es", nullable=False, comment="Código de idioma (es, en, etc)"
    )
    timezone = Column(String(50), default="UTC", nullable=False, comment="Zona horaria del usuario")

    # === RELACIÓN ===
    user = relationship("User", back_populates="profile")
    # created_at, updated_at → heredados de TimestampMixin

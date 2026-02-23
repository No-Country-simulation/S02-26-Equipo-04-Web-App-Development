from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin
from sqlalchemy.orm import relationship


class Video(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "videos"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    fps = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    codec = Column(String(50), nullable=True)
    bitrate = Column(Integer, nullable=True)
    has_audio = Column(Boolean, nullable=True)
    audio_codec = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)
    
    audios = relationship("Audio", back_populates="video", cascade="all, delete-orphan")
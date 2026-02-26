from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin


class Audio(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audios"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    sample_rate = Column(Integer, nullable=True)  # Hz: 44100, 48000, etc.
    channels = Column(Integer, nullable=True)  # 1=mono, 2=stereo, etc.
    codec = Column(String(50), nullable=True)  # mp3, aac, wav, etc.
    bitrate = Column(Integer, nullable=True)  # bits per second
    status = Column(String(50), nullable=True)  # pending, processing, completed, failed


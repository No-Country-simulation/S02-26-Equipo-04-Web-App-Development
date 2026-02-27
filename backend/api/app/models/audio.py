from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin


class Audio(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audios"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=True)

    duration_seconds = Column(Integer, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)

    codec = Column(String(50), nullable=True)
    bitrate = Column(Integer, nullable=True)

    status = Column(String(50), nullable=True)
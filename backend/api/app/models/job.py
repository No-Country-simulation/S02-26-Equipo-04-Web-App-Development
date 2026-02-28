from sqlalchemy import String, Column, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base
from app.models.enums import JobType, JobStatus
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin


class Job(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "jobs"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ahora es JSON
    output_path = Column(JSON, nullable=True)

    job_type = Column(Enum(JobType), default=JobType.REFRAME, name="job_type_enum", nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, name="job_status_enum", nullable=False, index=True)
    error_message = Column(String(500), nullable=True)

    video = relationship("Video")
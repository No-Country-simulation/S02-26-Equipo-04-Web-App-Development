from datetime import datetime
from sqlalchemy import Boolean, Column, String, DateTime
from app.database.base import Base
from app.models.base import UUIDAsPrimaryKeyMixin, TimestampMixin

class User(Base, UUIDAsPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

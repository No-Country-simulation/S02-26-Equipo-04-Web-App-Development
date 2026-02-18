"""
Pytest configuration and fixtures for testing.

SAFETY: All tests use SQLite in-memory database, never touching production/dev databases.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from fastapi.testclient import TestClient
from typing import Generator
from datetime import datetime
import uuid

from app.database.base import Base
from app.main import app
from app.core.dependencies import get_db
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash, create_access_token
from app.schemas.user import UserCreate


# ============================================================================
# UUID SUPPORT FOR SQLITE (PostgreSQL UUID -> SQLite STRING)
# ============================================================================

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            else:
                return value


# ============================================================================
# DATABASE FIXTURES (SQLite In-Memory - SAFE)
# ============================================================================

@pytest.fixture(scope="function")
def db_engine():
    """
    Creates a SQLite in-memory database engine for each test.
    
    Safety: Uses SQLite in-memory, completely isolated from production DB.
    Scope: function - each test gets a fresh database.
    """
    # Temporarily replace UUID columns with GUID (SQLite-compatible)
    from sqlalchemy.dialects import postgresql
    from app.models import user, profile
    
    # Store original column types
    original_types = {}
    
    for table_name, table in Base.metadata.tables.items():
        for column in table.columns:
            if isinstance(column.type, postgresql.UUID):
                original_types[(table_name, column.name)] = column.type
                column.type = GUID()
    
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup: drop all tables after test
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    
    # Restore original types
    for (table_name, column_name), original_type in original_types.items():
        Base.metadata.tables[table_name].columns[column_name].type = original_type


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """
    Provides a SQLAlchemy session for each test.
    
    Safety: Uses the in-memory engine, auto-rolls back after each test.
    Scope: function - each test gets an isolated session.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Provides a FastAPI TestClient with overridden database dependency.
    
    Safety: Overrides get_db() to use the test session instead of real DB.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ============================================================================
# USER FIXTURES (Test Data)
# ============================================================================

@pytest.fixture
def sample_user_data() -> dict:
    """Returns sample user registration data."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }


@pytest.fixture
def sample_user(db_session: Session, sample_user_data: dict) -> User:
    """
    Creates a test user in the database.
    
    Returns: User object with associated Profile.
    """
    user = User(
        email=sample_user_data["email"],
        hashed_password=get_password_hash(sample_user_data["password"]),
        is_active=True,
        is_verified=False,
        created_at=datetime.utcnow()
    )
    
    db_session.add(user)
    db_session.flush()
    
    # Create associated profile
    profile = Profile(user_id=user.id)
    db_session.add(profile)
    
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    """Creates an inactive test user."""
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("Password123!"),
        is_active=False,
        is_verified=False
    )
    
    db_session.add(user)
    db_session.flush()
    
    profile = Profile(user_id=user.id)
    db_session.add(profile)
    
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def verified_user(db_session: Session) -> User:
    """Creates a verified test user."""
    user = User(
        email="verified@example.com",
        hashed_password=get_password_hash("Password123!"),
        is_active=True,
        is_verified=True
    )
    
    db_session.add(user)
    db_session.flush()
    
    profile = Profile(user_id=user.id)
    db_session.add(profile)
    
    db_session.commit()
    db_session.refresh(user)
    
    return user


@pytest.fixture
def authenticated_user(sample_user: User) -> tuple[User, str]:
    """
    Returns a user with a valid JWT token.
    
    Returns: Tuple of (User, token_string)
    """
    token = create_access_token(subject=str(sample_user.id))
    return sample_user, token


@pytest.fixture
def auth_headers(authenticated_user: tuple[User, str]) -> dict:
    """Returns HTTP headers with Bearer token for authenticated requests."""
    _, token = authenticated_user
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# PROFILE FIXTURES
# ============================================================================

@pytest.fixture
def sample_profile_update() -> dict:
    """Returns sample profile update data."""
    return {
        "display_name": "Test User",
        "full_name": "Test Full Name",
        "bio": "This is a test bio",
        "preferred_language": "es",
        "timezone": "America/Argentina/Buenos_Aires"
    }


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def multiple_users(db_session: Session) -> list[User]:
    """Creates multiple test users for bulk testing."""
    users = []
    
    for i in range(5):
        user = User(
            email=f"user{i}@example.com",
            hashed_password=get_password_hash(f"Password{i}!"),
            is_active=True,
            is_verified=i % 2 == 0  # Alternate verified status
        )
        db_session.add(user)
        db_session.flush()
        
        profile = Profile(user_id=user.id)
        db_session.add(profile)
        
        users.append(user)
    
    db_session.commit()
    
    for user in users:
        db_session.refresh(user)
    
    return users

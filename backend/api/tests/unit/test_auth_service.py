"""
Unit tests for AuthService.

Safety: All tests use SQLite in-memory database via fixtures.
Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from jose import jwt

from app.services.auth_service import AuthService
from app.models.user import User
from app.models.profile import Profile
from app.schemas.user import UserCreate
from app.schemas.token import Token
from app.core.security import verify_password, get_password_hash
from app.core.config import settings
from app.utils.exceptions import (
    InvalidCredentialsException,
    InactiveUserException,
    UserAlreadyExistsException
)


class TestAuthServiceRegister:
    """Tests for user registration functionality."""
    
    def test_register_user_success(self, db_session: Session):
        """
        Test: User registers successfully with valid email and password.
        
        Validates:
        - User is created in database
        - Password is hashed (not stored as plaintext)
        - User is active by default
        - User is not verified by default
        - Profile is auto-created and associated
        """
        # Arrange
        service = AuthService(db_session)
        user_data = UserCreate(
            email="newuser@example.com",
            password="SecurePass123!"
        )
        
        # Act
        user = service.register_user(user_data)
        
        # Assert
        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.hashed_password is not None
        assert user.hashed_password != "SecurePass123!"  # Password is hashed
        assert verify_password("SecurePass123!", user.hashed_password) is True
        assert user.is_active is True
        assert user.is_verified is False
        assert user.created_at is not None
        
        # Verify profile was created
        profile = db_session.query(Profile).filter(Profile.user_id == user.id).first()
        assert profile is not None
        assert profile.user_id == user.id
    
    def test_register_user_duplicate_email(self, db_session: Session, sample_user: User):
        """
        Test: Registration fails when email already exists.
        
        Validates:
        - UserAlreadyExistsException is raised
        - No new user is created
        - Database remains unchanged
        """
        # Arrange
        service = AuthService(db_session)
        user_data = UserCreate(
            email=sample_user.email,  # Email already exists
            password="AnotherPass123!"
        )
        
        initial_count = db_session.query(User).count()
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsException):
            service.register_user(user_data)
        
        # Verify no new user was created
        final_count = db_session.query(User).count()
        assert final_count == initial_count
    
    def test_register_user_creates_profile(self, db_session: Session):
        """
        Test: Profile is automatically created when user registers.
        
        Validates:
        - Profile exists after registration
        - Profile is linked to user via user_id
        - Profile has default values
        """
        # Arrange
        service = AuthService(db_session)
        user_data = UserCreate(
            email="withprofile@example.com",
            password="Pass123!"
        )
        
        # Act
        user = service.register_user(user_data)
        
        # Assert
        profile = db_session.query(Profile).filter(Profile.user_id == user.id).first()
        assert profile is not None
        assert profile.user_id == user.id
        assert profile.preferred_language == "es"  # Default value
        assert profile.timezone == "UTC"  # Default value
    
    def test_register_user_password_is_hashed(self, db_session: Session):
        """
        Test: Password is properly hashed using bcrypt.
        
        Validates:
        - Password is not stored in plaintext
        - Hash is different from original password
        - Hash can be verified with original password
        """
        # Arrange
        service = AuthService(db_session)
        plain_password = "MySecretPassword123!"
        user_data = UserCreate(
            email="hashtest@example.com",
            password=plain_password
        )
        
        # Act
        user = service.register_user(user_data)
        
        # Assert
        assert user.hashed_password != plain_password
        assert len(user.hashed_password) > 50  # Bcrypt hashes are long
        assert verify_password(plain_password, user.hashed_password) is True
        assert verify_password("WrongPassword", user.hashed_password) is False
    
    def test_register_user_default_values(self, db_session: Session):
        """
        Test: User is created with correct default values.
        
        Validates:
        - is_active defaults to True
        - is_verified defaults to False
        - is_banned defaults to False
        - created_at is set
        """
        # Arrange
        service = AuthService(db_session)
        user_data = UserCreate(
            email="defaults@example.com",
            password="Pass123!"
        )
        
        # Act
        user = service.register_user(user_data)
        
        # Assert
        assert user.is_active is True
        assert user.is_verified is False
        assert user.is_banned is False
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)


class TestAuthServiceAuthenticate:
    """Tests for user authentication functionality."""
    
    def test_authenticate_user_success(self, db_session: Session, sample_user: User, sample_user_data: dict):
        """
        Test: User authenticates successfully with correct credentials.
        
        Validates:
        - User object is returned
        - last_login_at is updated
        - No exception is raised
        """
        # Arrange
        service = AuthService(db_session)
        email = sample_user_data["email"]
        password = sample_user_data["password"]
        
        original_login = sample_user.last_login_at
        
        # Act
        authenticated_user = service.authenticate_user(email, password)
        
        # Assert
        assert authenticated_user.id == sample_user.id
        assert authenticated_user.email == email
        assert authenticated_user.last_login_at is not None
        assert authenticated_user.last_login_at != original_login
    
    def test_authenticate_user_wrong_password(self, db_session: Session, sample_user: User):
        """
        Test: Authentication fails with incorrect password.
        
        Validates:
        - InvalidCredentialsException is raised
        - last_login_at is not updated
        """
        # Arrange
        service = AuthService(db_session)
        original_login = sample_user.last_login_at
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            service.authenticate_user(sample_user.email, "WrongPassword123!")
        
        # Verify last_login_at was not updated
        db_session.refresh(sample_user)
        assert sample_user.last_login_at == original_login
    
    def test_authenticate_user_nonexistent_email(self, db_session: Session):
        """
        Test: Authentication fails with non-existent email.
        
        Validates:
        - InvalidCredentialsException is raised
        - No user is returned
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            service.authenticate_user("notexist@example.com", "AnyPassword123!")
    
    def test_authenticate_inactive_user(self, db_session: Session, inactive_user: User):
        """
        Test: Authentication fails when user is inactive.
        
        Validates:
        - InactiveUserException is raised
        - Even with correct password, inactive users cannot login
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act & Assert
        with pytest.raises(InactiveUserException):
            service.authenticate_user(inactive_user.email, "Password123!")
    
    def test_authenticate_user_updates_last_login(self, db_session: Session, sample_user: User, sample_user_data: dict):
        """
        Test: last_login_at is updated on successful authentication.
        
        Validates:
        - last_login_at changes after login
        - Timestamp is recent (within last minute)
        """
        # Arrange
        service = AuthService(db_session)
        sample_user.last_login_at = datetime(2020, 1, 1)  # Old date
        db_session.commit()
        
        # Act
        service.authenticate_user(sample_user_data["email"], sample_user_data["password"])
        
        # Assert
        db_session.refresh(sample_user)
        assert sample_user.last_login_at > datetime(2020, 1, 1)
        assert sample_user.last_login_at > datetime.utcnow() - timedelta(minutes=1)
    
    def test_authenticate_case_sensitive_email(self, db_session: Session, sample_user: User, sample_user_data: dict):
        """
        Test: Email authentication is case-sensitive.
        
        Validates:
        - Email with different case fails authentication
        """
        # Arrange
        service = AuthService(db_session)
        uppercase_email = sample_user_data["email"].upper()
        
        # Act & Assert
        with pytest.raises(InvalidCredentialsException):
            service.authenticate_user(uppercase_email, sample_user_data["password"])


class TestAuthServiceCreateToken:
    """Tests for JWT token creation functionality."""
    
    def test_create_token_success(self, db_session: Session, sample_user: User):
        """
        Test: JWT token is created successfully for authenticated user.
        
        Validates:
        - Token object is returned
        - access_token is not empty
        - token_type is "bearer"
        - expires_in matches configuration
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act
        token = service.create_token_for_user(sample_user)
        
        # Assert
        assert isinstance(token, Token)
        assert token.access_token is not None
        assert len(token.access_token) > 0
        assert token.token_type == "bearer"
        assert token.expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    def test_create_token_valid_jwt(self, db_session: Session, sample_user: User):
        """
        Test: Generated token is a valid JWT.
        
        Validates:
        - Token can be decoded
        - Contains correct user ID in "sub" claim
        - Contains expiration time
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act
        token = service.create_token_for_user(sample_user)
        
        # Decode and verify
        payload = jwt.decode(
            token.access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Assert
        assert payload["sub"] == str(sample_user.id)
        assert "exp" in payload
        assert isinstance(payload["exp"], int)
    
    def test_create_token_expiration(self, db_session: Session, sample_user: User):
        """
        Test: Token has correct expiration time.
        
        Validates:
        - Expiration is in the future
        - Expiration matches configured duration
        """
        # Arrange
        service = AuthService(db_session)
        before_time = datetime.utcnow()
        
        # Act
        token = service.create_token_for_user(sample_user)
        
        # Decode
        payload = jwt.decode(
            token.access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        exp_datetime = datetime.fromtimestamp(payload["exp"])
        expected_exp = before_time + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Assert (allow 5 seconds tolerance)
        assert abs((exp_datetime - expected_exp).total_seconds()) < 5
    
    def test_create_token_unique_per_call(self, db_session: Session, sample_user: User):
        """
        Test: Token generation with time delay creates different tokens.
        
        Validates:
        - Tokens created at different times have different expirations
        - Token structure is valid
        """
        # Arrange
        service = AuthService(db_session)
        import time
        
        # Act
        token1 = service.create_token_for_user(sample_user)
        time.sleep(1)  # 1 second delay to ensure different expiration time
        token2 = service.create_token_for_user(sample_user)
        
        # Assert - Tokens should be different due to different expiration times
        assert token1.access_token != token2.access_token
        assert isinstance(token1.access_token, str)
        assert isinstance(token2.access_token, str)
    
    def test_create_token_contains_user_id(self, db_session: Session, verified_user: User):
        """
        Test: Token payload contains the correct user ID.
        
        Validates:
        - "sub" claim exists
        - "sub" value matches user.id
        - ID is stored as string (UUID serialization)
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act
        token = service.create_token_for_user(verified_user)
        
        # Decode
        payload = jwt.decode(
            token.access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Assert
        assert "sub" in payload
        assert payload["sub"] == str(verified_user.id)


class TestAuthServiceIntegration:
    """Integration tests for complete authentication flows."""
    
    def test_register_and_authenticate_flow(self, db_session: Session):
        """
        Test: Complete flow from registration to authentication.
        
        Validates:
        - User can register
        - Same user can authenticate immediately
        - Token is valid
        """
        # Arrange
        service = AuthService(db_session)
        user_data = UserCreate(
            email="flowtest@example.com",
            password="FlowPass123!"
        )
        
        # Act - Register
        user = service.register_user(user_data)
        
        # Act - Authenticate
        auth_user = service.authenticate_user("flowtest@example.com", "FlowPass123!")
        
        # Act - Create Token
        token = service.create_token_for_user(auth_user)
        
        # Assert
        assert user.id == auth_user.id
        assert token.access_token is not None
    
    def test_multiple_users_independent(self, db_session: Session):
        """
        Test: Multiple users can register and authenticate independently.
        
        Validates:
        - Multiple registrations work
        - Each user has unique credentials
        - Users don't interfere with each other
        """
        # Arrange
        service = AuthService(db_session)
        
        # Act - Register multiple users
        user1 = service.register_user(UserCreate(email="user1@test.com", password="SecurePass1!"))
        user2 = service.register_user(UserCreate(email="user2@test.com", password="SecurePass2!"))
        
        # Act - Authenticate each
        auth1 = service.authenticate_user("user1@test.com", "SecurePass1!")
        auth2 = service.authenticate_user("user2@test.com", "SecurePass2!")
        
        # Assert
        assert user1.id != user2.id
        assert auth1.id == user1.id
        assert auth2.id == user2.id
        
        # Verify wrong credentials don't work
        with pytest.raises(InvalidCredentialsException):
            service.authenticate_user("user1@test.com", "SecurePass2!")  # Wrong password

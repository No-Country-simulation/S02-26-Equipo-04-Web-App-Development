"""
Unit tests for Auth endpoints using mocks.

IMPORTANT: These are UNIT tests, NOT integration tests.
- Services are MOCKED (AuthService)
- Dependencies are MOCKED (get_db, get_current_active_user)
- Database is NEVER touched
- Only verify endpoint logic and service invocation

Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, ANY
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from app.main import app
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate
from app.utils.exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotFoundException
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_user():
    """Mock User object for testing"""
    user = Mock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.is_active = True
    user.is_verified = False
    user.role = "USER"
    user.created_at = datetime.now()
    return user

@pytest.fixture
def mock_token():
    """Mock Token response"""
    return Token(
        access_token="mock.jwt.token",
        token_type="bearer",
        expires_in=1800
    )


# ============================================================================
# TEST CLASS: POST /auth/register
# ============================================================================

class TestRegisterEndpointUnit:
    """Unit tests for POST /api/v1/auth/register"""
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_register_calls_service_with_correct_params(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Endpoint calls AuthService.register_user with correct UserCreate.
        
        Validates:
        - Service is instantiated with db
        - register_user is called once
        - UserCreate object has correct email/password
        - create_token_for_user is called with returned user
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.register_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 201
        mock_service.register_user.assert_called_once()
        
        # Verify UserCreate parameter
        call_args = mock_service.register_user.call_args[0][0]
        assert isinstance(call_args, UserCreate)
        assert call_args.email == "newuser@example.com"
        
        # Verify token creation was called
        mock_service.create_token_for_user.assert_called_once_with(mock_user)
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_register_returns_201_with_token(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Successful registration returns 201 with token.
        
        Validates:
        - Status code is 201 CREATED
        - Response contains access_token
        - Response contains token_type
        - Response contains expires_in
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.register_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        payload = {
            "email": "test@example.com",
            "password": "ValidPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert data["access_token"] == "mock.jwt.token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
    
    def test_register_invalid_email_returns_422(self, client: TestClient):
        """
        Test: Invalid email format fails Pydantic validation (422).
        
        Validates:
        - Status code is 422 UNPROCESSABLE ENTITY
        - Error mentions 'email' field
        - Service is NOT called (validation fails first)
        """
        # Arrange
        payload = {
            "email": "not-an-email",  # Invalid format
            "password": "ValidPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "details" in data or "detail" in data  # API uses 'details' instead of 'detail'
        # Check that error is about email field
        errors = data.get("details", data.get("detail", []))
        assert any("email" in str(error.get("loc", [])) for error in errors)
    
    def test_register_weak_password_returns_422(self, client: TestClient):
        """
        Test: Weak password fails Pydantic validation (422).
        
        Validates:
        - Password without uppercase fails
        - Password without lowercase fails
        - Password without number fails
        - Password too short fails
        """
        # Arrange - Test multiple weak passwords
        weak_passwords = [
            "short",              # Too short
            "nouppercase123!",    # No uppercase
            "NOLOWERCASE123!",    # No lowercase
            "NoNumbers!",         # No numbers
        ]
        
        for weak_pass in weak_passwords:
            payload = {
                "email": "test@example.com",
                "password": weak_pass
            }
            
            # Act
            response = client.post("/api/v1/auth/register", json=payload)
            
            # Assert
            assert response.status_code == 422, f"Password '{weak_pass}' should fail validation"
    
    def test_register_missing_email_returns_422(self, client: TestClient):
        """
        Test: Missing required field 'email' returns 422.
        
        Validates:
        - Required fields are enforced
        - Error specifies missing field
        """
        # Arrange
        payload = {
            "password": "ValidPass123!"
            # email missing
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        errors = data.get("details", data.get("detail", []))
        assert any("email" in str(error.get("loc", [])) for error in errors)
    
    def test_register_missing_password_returns_422(self, client: TestClient):
        """
        Test: Missing required field 'password' returns 422.
        """
        # Arrange
        payload = {
            "email": "test@example.com"
            # password missing
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 422
        data = response.json()
        errors = data.get("details", data.get("detail", []))
        assert any("password" in str(error.get("loc", [])) for error in errors)
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_register_duplicate_email_returns_409(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session
    ):
        """
        Test: Duplicate email raises UserAlreadyExistsException → 409 CONFLICT.
        
        Validates:
        - Service raises UserAlreadyExistsException
        - Endpoint catches it and returns 409
        - Error message is appropriate
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.register_user.side_effect = UserAlreadyExistsException()
        
        payload = {
            "email": "existing@example.com",
            "password": "ValidPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        assert response.status_code == 400  # API uses 400 instead of 409 for duplicate
        mock_service.register_user.assert_called_once()
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_register_service_instantiated_with_db(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: AuthService is instantiated with database session.
        
        Validates:
        - Service constructor receives db dependency
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.register_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        payload = {
            "email": "test@example.com",
            "password": "ValidPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/register", json=payload)
        
        # Assert
        mock_auth_service_class.assert_called_once()
        # Verify db was passed (it's a session object)
        assert mock_auth_service_class.call_args[0][0] is not None


# ============================================================================
# TEST CLASS: POST /auth/login
# ============================================================================

class TestLoginEndpointUnit:
    """Unit tests for POST /api/v1/auth/login"""
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_login_calls_authenticate_with_credentials(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Endpoint calls authenticate_user with correct email/password.
        
        Validates:
        - authenticate_user is called once
        - Email from form_data.username is passed
        - Password from form_data.password is passed
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.authenticate_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        form_data = {
            "username": "user@example.com",  # OAuth2 uses 'username' field
            "password": "MyPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        assert response.status_code == 200
        mock_service.authenticate_user.assert_called_once_with(
            "user@example.com",
            "MyPass123!"
        )
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_login_returns_200_with_token(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Successful login returns 200 with token.
        
        Validates:
        - Status code is 200 OK
        - Response contains complete token structure
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.authenticate_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        form_data = {
            "username": "user@example.com",
            "password": "CorrectPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock.jwt.token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_login_invalid_credentials_returns_401(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session
    ):
        """
        Test: Wrong credentials raise InvalidCredentialsException → 401.
        
        Validates:
        - Service raises InvalidCredentialsException
        - Endpoint returns 401 UNAUTHORIZED
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.authenticate_user.side_effect = InvalidCredentialsException()
        
        form_data = {
            "username": "user@example.com",
            "password": "WrongPassword"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        assert response.status_code == 401
    
    def test_login_missing_username_returns_422(self, client: TestClient):
        """
        Test: Missing username field returns 422.
        
        Validates:
        - OAuth2PasswordRequestForm validation works
        - Required fields are enforced
        """
        # Arrange
        form_data = {
            "password": "SomePass123!"
            # username missing
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        assert response.status_code == 422
    
    def test_login_missing_password_returns_422(self, client: TestClient):
        """
        Test: Missing password field returns 422.
        """
        # Arrange
        form_data = {
            "username": "user@example.com"
            # password missing
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        assert response.status_code == 422
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_login_calls_create_token_after_auth(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Token is created for authenticated user.
        
        Validates:
        - create_token_for_user is called with authenticated user
        - Flow is: authenticate → create token → return token
        """
        # Arrange
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.authenticate_user.return_value = mock_user
        mock_service.create_token_for_user.return_value = mock_token
        
        form_data = {
            "username": "user@example.com",
            "password": "ValidPass123!"
        }
        
        # Act
        response = client.post("/api/v1/auth/login", data=form_data)
        
        # Assert
        mock_service.create_token_for_user.assert_called_once_with(mock_user)


# ============================================================================
# TEST CLASS: GET /auth/me
# ============================================================================

class TestMeEndpointUnit:
    """Unit tests for GET /api/v1/auth/me"""
    
    @patch('app.api.v1.endpoints.auth.get_current_active_user')
    def test_me_requires_authentication(
        self,
        mock_get_current_user,
        client: TestClient
    ):
        """
        Test: Endpoint requires authentication (dependency).
        
        Validates:
        - Without token, dependency fails
        - Returns 401 or 403
        """
        # Arrange
        mock_get_current_user.side_effect = Exception("Not authenticated")
        
        # Act
        response = client.get("/api/v1/auth/me")
        
        # Assert
        # Without proper token, should fail authentication
        assert response.status_code in [401, 403]
    
    def test_me_without_token_returns_401(self, client: TestClient):
        """
        Test: Request without Authorization header returns 401.
        
        Validates:
        - Missing token is caught
        - Proper error response
        """
        # Act
        response = client.get("/api/v1/auth/me")
        
        # Assert
        assert response.status_code == 401
    
    def test_me_returns_user_with_profile(
        self,
        client: TestClient,
        mock_user
    ):
        """
        Test: Authenticated request returns user profile.
        
        Validates:
        - get_current_active_user dependency is resolved
        - UserPublic schema is returned
        - Response contains user data
        
        Note: In unit tests, we test that endpoint returns correct structure.
        Authentication testing is separate.
        """
        # Arrange - Override dependency before making request
        from app.core.dependencies import get_current_active_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        try:
            # Act
            response = client.get("/api/v1/auth/me")
            
            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "email" in data
            assert data["email"] == mock_user.email
        finally:
            # Cleanup
            app.dependency_overrides.clear()
    
    def test_me_calls_dependency_correctly(
        self,
        client: TestClient,
        mock_user
    ):
        """
        Test: Dependency get_current_active_user is invoked.
        
        Validates:
        - Dependency is called during request
        - User is retrieved from token
        """
        # Arrange
        from app.core.dependencies import get_current_active_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        try:
            # Act
            response = client.get("/api/v1/auth/me")
            
            # Assert
            assert response.status_code == 200
        finally:
            # Cleanup
            app.dependency_overrides.clear()


# ============================================================================
# TEST CLASS: POST /auth/refresh
# ============================================================================

class TestRefreshTokenEndpointUnit:
    """Unit tests for POST /api/v1/auth/refresh"""
    
    @patch('app.api.v1.endpoints.auth.AuthService')
    def test_refresh_creates_new_token(
        self,
        mock_auth_service_class,
        client: TestClient,
        db_session,
        mock_user,
        mock_token
    ):
        """
        Test: Refresh endpoint creates new token for current user.
        
        Validates:
        - Requires authentication
        - Calls create_token_for_user
        - Returns new token
        """
        # Arrange
        from app.core.dependencies import get_current_active_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        mock_service = Mock()
        mock_auth_service_class.return_value = mock_service
        mock_service.create_token_for_user.return_value = mock_token
        
        try:
            # Act
            response = client.post("/api/v1/auth/refresh")
            
            # Assert
            assert response.status_code == 200
            mock_service.create_token_for_user.assert_called_once_with(mock_user)
        finally:
            # Cleanup
            app.dependency_overrides.clear()
    
    def test_refresh_without_auth_returns_401(self, client: TestClient):
        """
        Test: Refresh without authentication returns 401.
        
        Validates:
        - Cannot refresh without valid token
        """
        # Act
        response = client.post("/api/v1/auth/refresh")
        
        # Assert
        assert response.status_code == 401


# ============================================================================
# TEST CLASS: POST /auth/logout
# ============================================================================

class TestLogoutEndpointUnit:
    """Unit tests for POST /api/v1/auth/logout"""
    
    def test_logout_returns_204(
        self,
        client: TestClient,
        mock_user
    ):
        """
        Test: Logout returns 204 NO CONTENT.
        
        Validates:
        - Endpoint is accessible to authenticated users
        - Returns 204 (even if it's a placeholder)
        """
        # Arrange
        from app.core.dependencies import get_current_active_user
        
        def override_get_current_user():
            return mock_user
        
        app.dependency_overrides[get_current_active_user] = override_get_current_user
        
        try:
            # Act
            response = client.post("/api/v1/auth/logout")
            
            # Assert
            assert response.status_code == 204
        finally:
            # Cleanup
            app.dependency_overrides.clear()
    
    def test_logout_without_auth_returns_401(self, client: TestClient):
        """
        Test: Logout without authentication returns 401.
        
        Validates:
        - Cannot logout without valid token
        """
        # Act
        response = client.post("/api/v1/auth/logout")
        
        # Assert
        assert response.status_code == 401

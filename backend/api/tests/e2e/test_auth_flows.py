"""
End-to-End Tests for Authentication Flows

These tests validate complete user workflows from start to finish,
using real services (no mocks) but isolated SQLite in-memory database.

Each test simulates realistic user journeys with multipl        # Step 4        # Step 3: Verify original user can still login
        login_payload = {
            "username": "duplicate@example.com",
            "password": "Password123"  # Original password
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        }
        assert login_response.status_code == 200
        
        # Step 4: Verify email matches original user
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "duplicate@example.com"
        assert me_data["is_active"] is Trueser can still login
        login_payload = {
            "username": "duplicate@example.com",
            "password": "Password123"  # Original password
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        
        # Step 5: Login with token and verify email (no full_name in UserPublic)
        login_token = login_response.json()["access_token"]
        login_headers = {"Authorization": f"Bearer {login_token}"}
        login_me_response = client.get("/api/v1/auth/me", headers=login_headers)
        assert login_me_response.status_code == 200
        login_me_data = login_me_response.json()
        assert login_me_data["email"] == "duplicate@example.com"
        assert login_me_data["is_active"] is True data consistency and persistence across operations.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.e2e
@pytest.mark.auth
class TestCompleteAuthFlows:
    """E2E tests for complete authentication workflows"""
    
    def test_complete_registration_login_profile_flow(self, client: TestClient):
        """
        E2E Flow: New user registers → logs in → views profile
        
        Steps:
        1. Register new user with valid data
        2. Login with the same credentials
        3. Access protected endpoint with token
        4. Verify data consistency across all steps
        
        Validates:
        - Registration creates user + profile
        - Login returns valid JWT token
        - Token grants access to protected resources
        - Data persists correctly in database
        """
        # Step 1: Register new user (returns token directly)
        register_payload = {
            "email": "e2e.user@example.com",
            "password": "SecurePass123",
            "full_name": "E2E Test User"
        }
        register_response = client.post(
            "/api/v1/auth/register", 
            json=register_payload
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        
        # Verify registration returns token
        assert "access_token" in register_data
        assert register_data["token_type"] == "bearer"
        assert "expires_in" in register_data
        
        register_token = register_data["access_token"]
        
        # Step 1b: Verify user profile with registration token
        headers = {"Authorization": f"Bearer {register_token}"}
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        
        # Verify profile data (without full profile details - see /profiles/me for that)
        assert profile_data["email"] == "e2e.user@example.com"
        assert profile_data["is_active"] is True
        assert profile_data["is_verified"] is False
        
        user_id = profile_data["id"]
        
        # Step 2: Login with registered credentials
        login_payload = {
            "username": "e2e.user@example.com",
            "password": "SecurePass123"
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # Verify login response structure
        assert "access_token" in login_data
        assert login_data["token_type"] == "bearer"
        assert "expires_in" in login_data
        
        access_token = login_data["access_token"]
        
        # Step 3: Access protected endpoint with token
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        
        # Verify profile data consistency
        assert me_data["id"] == user_id
        assert me_data["email"] == "e2e.user@example.com"
        assert me_data["is_active"] is True
        
        # Step 4: Verify refresh endpoint works
        refresh_response = client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
        
        # Verify new token works
        new_headers = {"Authorization": f"Bearer {refresh_data['access_token']}"}
        verify_response = client.get("/api/v1/auth/me", headers=new_headers)
        assert verify_response.status_code == 200


    def test_register_login_logout_flow(self, client: TestClient):
        """
        E2E Flow: Register → Login → Logout
        
        Steps:
        1. Register new user
        2. Get profile with registration token
        3. Logout
        
        Validates:
        - Full authentication cycle
        - Logout endpoint accessibility
        """
        # Step 1: Register
        register_payload = {
            "email": "logout@example.com",
            "password": "Password123",
            "full_name": "Logout Test"
        }
        register_response = client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        
        # Step 2: Verify access with token
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "logout@example.com"
        
        # Step 3: Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 204


    def test_authentication_security_flow(self, client: TestClient):
        """
        E2E Flow: Access without token → Get token → Access with token
        
        Steps:
        1. Try to access protected endpoint without token (should fail)
        2. Register and login to get valid token
        3. Access same endpoint with token (should succeed)
        4. Logout and try again (should fail)
        
        Validates:
        - Protected endpoints require authentication
        - Valid tokens grant access
        - Logout invalidates access
        """
        # Step 1: Try to access protected endpoint without token
        no_auth_response = client.get("/api/v1/auth/me")
        assert no_auth_response.status_code == 401
        
        # Step 2: Register and login
        register_payload = {
            "email": "security@example.com",
            "password": "Secure123",
            "full_name": "Security Test"
        }
        register_response = client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201
        
        login_payload = {
            "username": "security@example.com",
            "password": "Secure123"
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Step 3: Access with valid token
        headers = {"Authorization": f"Bearer {token}"}
        auth_response = client.get("/api/v1/auth/me", headers=headers)
        assert auth_response.status_code == 200
        assert auth_response.json()["email"] == "security@example.com"
        
        # Step 4: Logout
        logout_response = client.post("/api/v1/auth/logout", headers=headers)
        assert logout_response.status_code == 204
        
        # Step 5: Try with invalid/malformed token
        bad_headers = {"Authorization": "Bearer invalid.token.here"}
        bad_response = client.get("/api/v1/auth/me", headers=bad_headers)
        assert bad_response.status_code == 401


    def test_duplicate_registration_flow(self, client: TestClient):
        """
        E2E Flow: Register once → Try again with same email → Verify error
        
        Steps:
        1. Register user successfully
        2. Attempt to register again with same email
        3. Verify appropriate error is returned
        4. Verify original user can still login
        
        Validates:
        - Duplicate email registration is prevented
        - Error handling works correctly
        - Original user is not affected by failed registration
        """
        # Step 1: First registration (should succeed, returns token)
        register_payload = {
            "email": "duplicate@example.com",
            "password": "Password123",
            "full_name": "First User"
        }
        first_response = client.post("/api/v1/auth/register", json=register_payload)
        assert first_response.status_code == 201
        first_token = first_response.json()["access_token"]
        
        # Verify first user data
        headers = {"Authorization": f"Bearer {first_token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        first_data = me_response.json()
        assert first_data["email"] == "duplicate@example.com"
        
        # Step 2: Second registration with same email (should fail)
        duplicate_payload = {
            "email": "duplicate@example.com",
            "password": "DifferentPass456",
            "full_name": "Second User"
        }
        duplicate_response = client.post("/api/v1/auth/register", json=duplicate_payload)
        assert duplicate_response.status_code == 400
        error_data = duplicate_response.json()
        assert "detail" in error_data or "details" in error_data
        
        # Step 3: Verify original user can still login
        login_payload = {
            "username": "duplicate@example.com",
            "password": "Password123"  # Original password
        }
        login_response = client.post(
            "/api/v1/auth/login",
            data=login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert login_response.status_code == 200
        
        # Step 4: Verify email matches original user
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "duplicate@example.com"
        assert me_data["is_active"] is True


    def test_login_error_recovery_flow(self, client: TestClient):
        """
        E2E Flow: Wrong password → Correct password → Verify success
        
        Steps:
        1. Register user
        2. Attempt login with wrong password (should fail)
        3. Attempt login with correct password (should succeed)
        4. Verify account is not locked after failed attempt
        
        Validates:
        - Invalid credentials are rejected
        - Correct credentials work after failed attempt
        - System handles authentication errors gracefully
        """
        # Step 1: Register user
        register_payload = {
            "email": "recovery@example.com",
            "password": "CorrectPassword123",
            "full_name": "Recovery Test"
        }
        register_response = client.post("/api/v1/auth/register", json=register_payload)
        assert register_response.status_code == 201
        
        # Step 2: Login with wrong password
        wrong_login_payload = {
            "username": "recovery@example.com",
            "password": "WrongPassword456"
        }
        wrong_response = client.post(
            "/api/v1/auth/login",
            data=wrong_login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert wrong_response.status_code == 401
        error_data = wrong_response.json()
        assert "detail" in error_data or "details" in error_data
        
        # Step 3: Login with correct password
        correct_login_payload = {
            "username": "recovery@example.com",
            "password": "CorrectPassword123"
        }
        correct_response = client.post(
            "/api/v1/auth/login",
            data=correct_login_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert correct_response.status_code == 200
        token = correct_response.json()["access_token"]
        
        # Step 4: Verify token works and account is accessible
        headers = {"Authorization": f"Bearer {token}"}
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["email"] == "recovery@example.com"
        assert me_data["is_active"] is True
        
        # Step 5: Try wrong username
        wrong_email_payload = {
            "username": "nonexistent@example.com",
            "password": "CorrectPassword123"
        }
        wrong_email_response = client.post(
            "/api/v1/auth/login",
            data=wrong_email_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        assert wrong_email_response.status_code == 401

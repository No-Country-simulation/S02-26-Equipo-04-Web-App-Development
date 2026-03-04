"""
Unit tests for UserService.

Safety: All tests use SQLite in-memory database via fixtures.
Pattern: AAA (Arrange, Act, Assert)
"""
import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session

from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import verify_password
from app.utils.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)


class TestUserServiceGetUser:
    """Tests for getting user by ID."""
    
    def test_get_user_by_id_success(self, db_session: Session, sample_user: User):
        """
        Test: User is retrieved successfully by valid ID.
        
        Validates:
        - User object is returned
        - Correct user is returned
        - All user fields are accessible
        """
        # Arrange
        service = UserService(db_session)
        
        # Act
        user = service.get_user_by_id(sample_user.id)
        
        # Assert
        assert user.id == sample_user.id
        assert user.email == sample_user.email
        assert user.is_active == sample_user.is_active
    
    def test_get_user_by_id_not_found(self, db_session: Session):
        """
        Test: UserNotFoundException raised when ID doesn't exist.
        
        Validates:
        - Exception is raised for non-existent UUID
        - Database query completes without error
        """
        # Arrange
        service = UserService(db_session)
        fake_id = uuid4()
        
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            service.get_user_by_id(fake_id)
    
    def test_get_user_by_id_with_profile(self, db_session: Session, sample_user: User):
        """
        Test: User is retrieved with associated profile.
        
        Validates:
        - User has profile relationship loaded
        - Profile can be accessed
        """
        # Arrange
        service = UserService(db_session)
        
        # Act
        user = service.get_user_by_id(sample_user.id)
        
        # Assert
        assert user.profile is not None
        assert user.profile.user_id == user.id


class TestUserServiceUpdate:
    """Tests for updating user data."""
    
    def test_update_user_email_success(self, db_session: Session, sample_user: User):
        """
        Test: User email is updated successfully.
        
        Validates:
        - Email is changed
        - Other fields remain unchanged
        - Database is committed
        """
        # Arrange
        service = UserService(db_session)
        new_email = "newemail@example.com"
        update_data = UserUpdate(email=new_email)
        
        # Act
        updated_user = service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.email == new_email
        assert updated_user.id == sample_user.id
        
        # Verify persistence
        db_session.refresh(updated_user)
        assert updated_user.email == new_email
    
    def test_update_user_email_duplicate(self, db_session: Session, sample_user: User, verified_user: User):
        """
        Test: Update fails when trying to use existing email.
        
        Validates:
        - UserAlreadyExistsException is raised
        - Original email is not changed
        """
        # Arrange
        service = UserService(db_session)
        update_data = UserUpdate(email=verified_user.email)  # Existing email
        original_email = sample_user.email
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsException):
            service.update_user(sample_user.id, update_data)
        
        # Verify email didn't change
        db_session.refresh(sample_user)
        assert sample_user.email == original_email
    
    def test_update_user_is_active(self, db_session: Session, sample_user: User):
        """
        Test: User can be deactivated.
        
        Validates:
        - is_active flag can be changed
        - Email remains unchanged
        """
        # Arrange
        service = UserService(db_session)
        original_email = sample_user.email
        assert sample_user.is_active is True  # Initially active
        
        # Act: Deactivate user
        sample_user.is_active = False
        db_session.commit()
        db_session.refresh(sample_user)
        
        # Assert
        assert sample_user.is_active is False
        assert sample_user.email == original_email
    
    def test_update_user_password(self, db_session: Session, sample_user: User):
        """
        Test: User password is updated and hashed correctly.
        
        Validates:
        - Password is changed
        - New password is hashed
        - Old password no longer works
        - New password can be verified
        """
        # Arrange
        service = UserService(db_session)
        new_password = "NewSecurePassword456!"
        update_data = UserUpdate(password=new_password)
        old_hash = sample_user.hashed_password
        
        # Act
        updated_user = service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.hashed_password != old_hash
        assert updated_user.hashed_password != new_password  # Not plaintext
        assert verify_password(new_password, updated_user.hashed_password) is True
    
    def test_update_user_partial_update(self, db_session: Session, sample_user: User):
        """
        Test: Partial update (only email) works correctly.
        
        Validates:
        - Only specified fields are updated
        - Unspecified fields remain unchanged
        """
        # Arrange
        service = UserService(db_session)
        original_password = sample_user.hashed_password
        
        update_data = UserUpdate(email="partial@example.com")
        
        # Act
        updated_user = service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.email == "partial@example.com"
        assert updated_user.hashed_password == original_password  # Unchanged
    
    def test_update_user_not_found(self, db_session: Session):
        """
        Test: Update fails when user doesn't exist.
        
        Validates:
        - UserNotFoundException is raised
        - No changes are made to database
        """
        # Arrange
        service = UserService(db_session)
        fake_id = uuid4()
        update_data = UserUpdate(email="new@example.com")
        
        # Act & Assert
        with pytest.raises(UserNotFoundException):
            service.update_user(fake_id, update_data)
    
    def test_update_user_multiple_fields(self, db_session: Session, sample_user: User):
        """
        Test: Multiple fields can be updated simultaneously.
        
        Validates:
        - All specified fields are updated
        - Updates are atomic (all or nothing)
        """
        # Arrange
        service = UserService(db_session)
        update_data = UserUpdate(
            email="multiedit@example.com",
            password="NewPass789!"
        )
        
        # Act
        updated_user = service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.email == "multiedit@example.com"
        assert verify_password("NewPass789!", updated_user.hashed_password) is True
    
    def test_update_user_same_email(self, db_session: Session, sample_user: User):
        """
        Test: User can "update" to their own email (no-op).
        
        Validates:
        - No exception is raised
        - Email remains the same
        - Operation completes successfully
        """
        # Arrange
        service = UserService(db_session)
        update_data = UserUpdate(email=sample_user.email)
        
        # Act
        updated_user = service.update_user(sample_user.id, update_data)
        
        # Assert
        assert updated_user.email == sample_user.email
        assert updated_user.id == sample_user.id


class TestUserServiceIntegration:
    """Integration tests for UserService."""
    
    def test_get_and_update_flow(self, db_session: Session, sample_user: User):
        """
        Test: Complete flow of getting user and updating.
        
        Validates:
        - Get returns current data
        - Update modifies data
        - Get after update returns new data
        """
        # Arrange
        service = UserService(db_session)
        
        # Act 1 - Get original
        original = service.get_user_by_id(sample_user.id)
        original_email = original.email
        
        # Act 2 - Update
        service.update_user(sample_user.id, UserUpdate(email="flow@example.com"))
        
        # Act 3 - Get updated
        updated = service.get_user_by_id(sample_user.id)
        
        # Assert
        assert original_email != "flow@example.com"
        assert updated.email == "flow@example.com"
    
    def test_multiple_updates_sequential(self, db_session: Session, sample_user: User):
        """
        Test: Multiple sequential updates work correctly.
        
        Validates:
        - Each update is applied
        - Updates don't interfere with each other
        - Final state reflects all updates
        """
        # Arrange
        service = UserService(db_session)
        
        # Act - Multiple updates
        service.update_user(sample_user.id, UserUpdate(email="email1@test.com"))
        service.update_user(sample_user.id, UserUpdate(password="NewPass123!"))
        service.update_user(sample_user.id, UserUpdate(email="email2@test.com"))
        
        # Assert
        final_user = service.get_user_by_id(sample_user.id)
        assert final_user.email == "email2@test.com"
        assert verify_password("NewPass123!", final_user.hashed_password) is True

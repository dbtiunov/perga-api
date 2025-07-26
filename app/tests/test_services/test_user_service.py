import pytest
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_utils import verify_password
from app.services.user_service import UserService


class TestUserService:
    """Tests for the UserService class"""

    def test_get_user_by_email(self, test_db: Session, test_user):
        """Test that get_user_by_email returns the correct user"""
        # Get the user by email
        db_user = UserService.get_user_by_email(test_db, test_user.email)
        assert db_user is not None
        assert db_user.id == test_user.id
        assert db_user.email == test_user.email

        # Try to get a non-existent user
        db_user = UserService.get_user_by_email(test_db, "nonexistent@example.com")
        assert db_user is None

    def test_get_user_by_username(self, test_db: Session, test_user):
        """Test that get_user_by_username returns the correct user"""
        # Set a username for the test user
        test_user.username = "testuser"
        test_db.commit()
        test_db.refresh(test_user)

        # Get the user by username
        db_user = UserService.get_user_by_username(test_db, "testuser")
        assert db_user is not None
        assert db_user.id == test_user.id
        assert db_user.username == "testuser"

        # Try to get a non-existent user
        db_user = UserService.get_user_by_username(test_db, "nonexistent")
        assert db_user is None

    def test_get_user_by_id(self, test_db: Session, test_user):
        """Test that get_user_by_id returns the correct user"""
        # Get the user by ID
        db_user = UserService.get_user_by_id(test_db, test_user.id)
        assert db_user is not None
        assert db_user.id == test_user.id
        assert db_user.email == test_user.email

        # Try to get a non-existent user
        db_user = UserService.get_user_by_id(test_db, 999)
        assert db_user is None

    def test_create_user(self, test_db: Session):
        """Test that create_user creates a user correctly"""
        # Create a user
        user_create = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123"
        )
        db_user = UserService.create_user(test_db, user_create)
        
        # Check that the user was created correctly
        assert db_user.id is not None
        assert db_user.username == "newuser"
        assert db_user.email == "newuser@example.com"
        assert verify_password("password123", db_user.hashed_password)
        assert db_user.is_active is True

    def test_create_user_duplicate_email(self, test_db: Session, test_user):
        """Test that create_user raises an error when email is already registered"""
        # Try to create a user with the same email
        user_create = UserCreate(
            username="newuser",
            email=test_user.email,
            password="password123"
        )
        
        # Should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            UserService.create_user(test_db, user_create)
        
        assert "Email already registered" in str(excinfo.value)

    def test_create_user_duplicate_username(self, test_db: Session):
        """Test that create_user raises an error when username is already taken"""
        # Create a user
        user_create1 = UserCreate(
            username="sameusername",
            email="user1@example.com",
            password="password123"
        )
        UserService.create_user(test_db, user_create1)
        
        # Try to create another user with the same username
        user_create2 = UserCreate(
            username="sameusername",
            email="user2@example.com",
            password="password123"
        )
        
        # Should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            UserService.create_user(test_db, user_create2)
        
        assert "Username already taken" in str(excinfo.value)

    def test_update_user(self, test_db: Session, test_user):
        """Test that update_user updates a user correctly"""
        # Update the user
        user_update = UserUpdate(
            email="updated@example.com"
        )
        db_user = UserService.update_user(test_db, test_user.id, user_update)
        
        # Check that the user was updated correctly
        assert db_user.id == test_user.id
        assert db_user.email == "updated@example.com"
        
        # Try to update a non-existent user
        db_user = UserService.update_user(test_db, 999, user_update)
        assert db_user is None

    def test_update_user_password(self, test_db: Session, test_user):
        """Test that update_user updates a user's password correctly"""
        # Update the user's password
        user_update = UserUpdate(
            password="newpassword123"
        )
        db_user = UserService.update_user(test_db, test_user.id, user_update)
        
        # Check that the password was updated correctly
        assert verify_password("newpassword123", db_user.hashed_password)

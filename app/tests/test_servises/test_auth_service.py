import pytest
from jose import jwt
from unittest.mock import patch

from app.services.auth_service import AuthService
from app.services.auth_utils import (
    SECRET_KEY, ALGORITHM,
    create_access_token, create_refresh_token, get_password_hash
)
from app.models.user import User


class TestAuthService:
    """Tests for the AuthService class"""

    def test_authenticate_user_success(self, test_db):
        """Test that authenticate_user returns the user when credentials are correct"""
        # Create a test user
        password = 'password123'
        user = User(
            username="testuser",
            email="auth_test@example.com",
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        test_db.add(user)
        test_db.commit()
        test_db.refresh(user)

        # Authenticate with correct credentials
        authenticated_user = AuthService.authenticate_user(test_db, user.username, password)
        
        assert authenticated_user is not None
        assert authenticated_user.id == user.id
        assert authenticated_user.email == "auth_test@example.com"

    def test_authenticate_user_wrong_password(self, test_db):
        """Test that authenticate_user returns None when password is incorrect"""
        # Create a test user
        user = User(
            username="testuser",
            email="auth_test@example.com",
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        test_db.add(user)
        test_db.commit()

        # Authenticate with wrong password
        authenticated_user = AuthService.authenticate_user(
            test_db, "auth_test@example.com", "wrong_password"
        )
        
        assert authenticated_user is None

    def test_authenticate_user_nonexistent(self, test_db):
        """Test that authenticate_user returns None when user doesn't exist"""
        # Authenticate with non-existent user
        authenticated_user = AuthService.authenticate_user(
            test_db, "nonexistent@example.com", "password123"
        )
        
        assert authenticated_user is None

    def test_create_user_tokens(self, test_user):
        """Test that create_user_tokens returns valid tokens"""
        # Create tokens for the test user
        tokens = AuthService.create_user_tokens(test_user.id)
        
        # Check that the response contains the expected keys
        assert "access_token" in tokens
        assert "token_type" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        
        # Decode the access token and verify its contents
        access_payload = jwt.decode(tokens["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert access_payload["sub"] == str(test_user.id)
        assert access_payload["token_type"] == "access"
        
        # Decode the refresh token and verify its contents
        refresh_payload = jwt.decode(tokens["refresh_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert refresh_payload["sub"] == str(test_user.id)
        assert refresh_payload["token_type"] == "refresh"

    def test_validate_refresh_token_valid(self, test_db, test_user):
        """Test that validate_refresh_token returns the user when token is valid"""
        # Create a refresh token for the test user
        refresh_token = create_refresh_token({"sub": test_user.id})
        
        # Validate the refresh token
        user = AuthService.validate_refresh_token(test_db, refresh_token)
        
        assert user is not None
        assert user.id == test_user.id

    def test_validate_refresh_token_invalid(self, test_db, test_user):
        """Test that validate_refresh_token returns None when token is invalid"""
        # Create an access token (not a refresh token)
        access_token = create_access_token({"sub": test_user.id})
        
        # Validate the access token as a refresh token (should fail)
        user = AuthService.validate_refresh_token(test_db, access_token)
        
        assert user is None
        
        # Create an invalid token
        invalid_token = "invalid.token.string"
        
        # Validate the invalid token
        user = AuthService.validate_refresh_token(test_db, invalid_token)
        
        assert user is None

    def test_validate_refresh_token_nonexistent_user(self, test_db):
        """Test that validate_refresh_token returns None when user doesn't exist"""
        # Create a refresh token for a non-existent user
        refresh_token = create_refresh_token({"sub": 999})
        
        # Validate the refresh token
        user = AuthService.validate_refresh_token(test_db, refresh_token)
        
        assert user is None

    @patch('app.services.auth_service.jwt.decode')
    async def test_get_current_user_success(self, mock_decode, test_db, test_user):
        """Test that get_current_user returns the user when token is valid"""
        # Mock the jwt.decode function to return a payload with the test user's ID
        mock_decode.return_value = {"sub": str(test_user.id)}
        
        # Get the current user
        user = await AuthService.get_current_user("valid_token", test_db)
        
        assert user is not None
        assert user.id == test_user.id
        
        # Verify that jwt.decode was called with the expected arguments
        mock_decode.assert_called_once_with("valid_token", SECRET_KEY, algorithms=[ALGORITHM])

    @patch('app.services.auth_service.jwt.decode')
    async def test_get_current_user_jwt_error(self, mock_decode, test_db):
        """Test that get_current_user raises an exception when token is invalid"""
        # Mock the jwt.decode function to raise a JWTError
        mock_decode.side_effect = jwt.JWTError()
        
        # Attempt to get the current user with an invalid token
        with pytest.raises(Exception) as excinfo:
            await AuthService.get_current_user("invalid_token", test_db)
        
        # Check that the exception is an HTTPException with status code 401
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail

    @patch('app.services.auth_service.jwt.decode')
    async def test_get_current_user_missing_sub(self, mock_decode, test_db):
        """Test that get_current_user raises an exception when sub is missing"""
        # Mock the jwt.decode function to return a payload without a sub claim
        mock_decode.return_value = {"token_type": "access"}
        
        # Attempt to get the current user with a token missing the sub claim
        with pytest.raises(Exception) as excinfo:
            await AuthService.get_current_user("token_without_sub", test_db)
        
        # Check that the exception is an HTTPException with status code 401
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail

    @patch('app.services.auth_service.jwt.decode')
    async def test_get_current_user_invalid_sub(self, mock_decode, test_db):
        """Test that get_current_user raises an exception when sub is invalid"""
        # Mock the jwt.decode function to return a payload with an invalid sub claim
        mock_decode.return_value = {"sub": "not_an_integer"}
        
        # Attempt to get the current user with a token with an invalid sub claim
        with pytest.raises(Exception) as excinfo:
            await AuthService.get_current_user("token_with_invalid_sub", test_db)
        
        # Check that the exception is an HTTPException with status code 401
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail

    @patch('app.services.auth_service.jwt.decode')
    async def test_get_current_user_nonexistent_user(self, mock_decode, test_db):
        """Test that get_current_user raises an exception when user doesn't exist"""
        # Mock the jwt.decode function to return a payload with a non-existent user ID
        mock_decode.return_value = {"sub": "999"}
        
        # Attempt to get the current user with a token for a non-existent user
        with pytest.raises(Exception) as excinfo:
            await AuthService.get_current_user("token_for_nonexistent_user", test_db)
        
        # Check that the exception is an HTTPException with status code 401
        assert excinfo.value.status_code == 401
        assert "Could not validate credentials" in excinfo.value.detail

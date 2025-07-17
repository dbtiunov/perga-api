from datetime import datetime, timedelta
from jose import jwt

from app.services.auth_utils import (
    get_password_hash, verify_password, create_token,
    create_access_token, create_refresh_token,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS
)


class TestAuthUtils:
    """Tests for the auth_utils module"""

    def test_password_hashing(self):
        """Test that password hashing and verification work correctly"""
        # Hash a password
        password = "test_password"
        hashed_password = get_password_hash(password)
        
        # Verify that the hash is different from the original password
        assert hashed_password != password
        
        # Verify that the password can be verified against the hash
        assert verify_password(password, hashed_password) is True
        
        # Verify that an incorrect password fails verification
        assert verify_password("wrong_password", hashed_password) is False
        
        # Verify that an invalid hash format is handled gracefully
        assert verify_password(password, "invalid_hash_format") is False

    def test_create_token(self):
        """Test that create_token creates a valid JWT token"""
        # Create a token with custom data
        data = {"sub": "123", "name": "Test User"}
        token = create_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["name"] == "Test User"
        assert payload["token_type"] == "access"
        
        # Verify that the token has an expiration time
        assert "exp" in payload
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.now()
        assert exp_time > now
        
        # Create a token with a custom expiration time
        custom_expires = timedelta(minutes=30)
        token = create_token(data, expires_delta=custom_expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp_time = datetime.now() + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_create_access_token(self):
        """Test that create_access_token creates a valid access token"""
        # Create an access token
        data = {"sub": "123"}
        token = create_access_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["token_type"] == "access"
        
        # Verify that the token has the default expiration time
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp_time = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5
        
        # Create an access token with a custom expiration time
        custom_expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=custom_expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp_time = datetime.now() + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_create_refresh_token(self):
        """Test that create_refresh_token creates a valid refresh token"""
        # Create a refresh token
        data = {"sub": "123"}
        token = create_refresh_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert payload["token_type"] == "refresh"
        
        # Verify that the token has the default expiration time
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp_time = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5
        
        # Create a refresh token with a custom expiration time
        custom_expires = timedelta(days=7)
        token = create_refresh_token(data, expires_delta=custom_expires)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        expected_exp_time = datetime.now() + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_token_with_integer_sub(self):
        """Test that create_token handles integer sub values correctly"""
        # Create a token with an integer sub
        data = {"sub": 123}
        token = create_token(data)
        
        # Decode the token and verify that sub is a string
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["sub"] == "123"
        assert isinstance(payload["sub"], str)

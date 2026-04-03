from datetime import datetime, timedelta, timezone
from jose import jwt

from app.const.auth import SIGNING_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, TokenType
from app.core.config import settings
from app.services.auth_utils import (
    generate_password_hash, validate_password, create_token,
    create_access_token, create_refresh_token,
)


class TestAuthUtils:
    """Tests for the auth_utils module"""
    TEST_USER_ID = 123
    TEST_USERNAME = 'testuser'
    TEST_PASSWORD = 'test_password'

    def test_password_hashing(self):
        """Test that password hashing and verification work correctly"""
        # Hash a password
        password = self.TEST_PASSWORD
        hashed_password = generate_password_hash(password)
        
        # Verify that the hash is different from the original password
        assert hashed_password != password
        
        # Verify that the password can be verified against the hash
        assert validate_password(password, hashed_password) is True
        
        # Verify that an incorrect password fails verification
        assert validate_password('wrong_password', hashed_password) is False
        
        # Verify that an invalid hash format is handled gracefully
        assert validate_password(password, 'invalid_hash_format') is False

    def test_create_token(self):
        """Test that create_token creates a valid JWT token"""
        # Create a token with custom data
        data = {"sub": str(self.TEST_USER_ID)}
        token = create_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        assert payload['sub'] == str(self.TEST_USER_ID)
        assert payload['token_type'] == TokenType.ACCESS
        
        # Verify that the token has an expiration time
        assert 'exp' in payload
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        assert exp_time > now
        
        # Create a token with a custom expiration time
        custom_expires = timedelta(minutes=30)
        token = create_token(data, custom_timeout=custom_expires)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_exp_time = datetime.now(timezone.utc) + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_create_access_token(self):
        """Test that create_access_token creates a valid access token"""
        # Create an access token
        data = {'sub': str(self.TEST_USER_ID)}
        token = create_access_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        assert payload['sub'] == str(self.TEST_USER_ID)
        assert payload['token_type'] == TokenType.ACCESS
        
        # Verify that the token has the default expiration time
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        expected_exp_time = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5
        
        # Create an access token with a custom expiration time
        custom_expires = timedelta(minutes=20)
        token = create_access_token(data, custom_timeout=custom_expires)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        expected_exp_time = datetime.now(timezone.utc) + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_create_refresh_token(self):
        """Test that create_refresh_token creates a valid refresh token"""
        # Create a refresh token
        data = {'sub': str(self.TEST_USER_ID)}
        token = create_refresh_token(data)
        
        # Decode the token and verify its contents
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        assert payload['sub'] == str(self.TEST_USER_ID)
        assert payload['token_type'] == TokenType.REFRESH
        
        # Verify that the token has the default expiration time
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        expected_exp_time = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5
        
        # Create a refresh token with a custom expiration time
        custom_expires = timedelta(days=7)
        token = create_refresh_token(data, custom_timeout=custom_expires)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        exp_time = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        expected_exp_time = datetime.now(timezone.utc) + custom_expires
        # Allow for a small difference due to processing time
        assert abs((exp_time - expected_exp_time).total_seconds()) < 5

    def test_token_with_integer_sub(self):
        """Test that create_token handles integer sub values correctly"""
        # Create a token with an integer sub
        data = {'sub': self.TEST_USER_ID}
        token = create_token(data)
        
        # Decode the token and verify that sub is a string
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[SIGNING_ALGORITHM])
        assert payload['sub'] == str(self.TEST_USER_ID)
        assert isinstance(payload['sub'], str)

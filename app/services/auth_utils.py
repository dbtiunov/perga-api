from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.core.config import settings

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def generate_password_hash(plain_password: str) -> str:
    """
    Hashes password using bcrypt:
    1. Converts plain password to bytes
    2. Generates salt
    3. Hashes password with salt
    4. Returns hashed bytes as string
    """
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')


def validate_password(plain_password: str, hashed_password: str) -> bool:
    """ Verifies a plain password against a hashed password """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
    except UnicodeEncodeError:
        return False

    try:
        result = bcrypt.checkpw(password_bytes, hashed_bytes)
    except ValueError:
        # invalid bcrypt hash format
        result = False

    return result


def create_token(data: dict, expires_delta: timedelta | None = None, token_type: str = "access") -> str:
    """
    Create a JWT token (access or refresh)

    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        token_type: Type of token ("access" or "refresh")

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    # Ensure 'sub' is a string if present
    if to_encode.get('sub'):
        to_encode["sub"] = str(to_encode["sub"])

    to_encode["token_type"] = token_type

    # Set expiration based on token type
    if expires_delta:
        expire_dt = datetime.now(timezone.utc) + expires_delta
    elif token_type == "refresh":
        expire_dt = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:  # access token by default
        expire_dt = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode['exp'] = expire_dt

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create an access token with default expiration of ACCESS_TOKEN_EXPIRE_MINUTES """
    return create_token(data, expires_delta, token_type="access")


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """ Create a refresh token with default expiration of REFRESH_TOKEN_EXPIRE_DAYS """
    return create_token(data, expires_delta, token_type="refresh")

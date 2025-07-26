from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib import exc as passlib_exc
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        result = pwd_context.verify(plain_password, hashed_password)
    except passlib_exc.UnknownHashError:
        # Handle case when hash format cannot be identified
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

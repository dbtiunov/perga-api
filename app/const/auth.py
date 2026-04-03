from enum import Enum


SIGNING_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    BEARER = "bearer"

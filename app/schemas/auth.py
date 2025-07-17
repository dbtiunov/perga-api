from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: Optional[int] = None
    exp: Optional[int] = None


class SigninRequest(BaseModel):
    """Schema for signin request."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str
    refresh_token: str | None = None


class TokenPayload(BaseModel):
    """Schema for token payload."""
    sub: int | None = None
    exp: int | None = None


class SigninRequest(BaseModel):
    """Schema for signin request."""
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

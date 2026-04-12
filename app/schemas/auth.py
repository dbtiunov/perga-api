from pydantic import BaseModel


class TokenSchema(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str | None = None


class SigninSchema(BaseModel):
    username: str
    password: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str

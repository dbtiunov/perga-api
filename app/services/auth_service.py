from datetime import timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import TokenPayload
from app.services.user_service import UserService
from app.services.auth_utils import (
    verify_password, create_access_token, create_refresh_token,
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/access_token/")


class AuthService:
    @classmethod
    def authenticate_user(cls, db: Session, username: str, password: str) -> User | None:
        user = UserService.get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    @classmethod
    def create_user_tokens(cls, user_id: int) -> dict:
        """ Returns dictionary with access_token, token_type, and refresh_token """
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = create_refresh_token(
            data={"sub": user_id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token
        }

    @classmethod
    def validate_refresh_token(cls, db: Session, refresh_token: str) -> User | None:
        """ Validate a refresh token and return the associated user """
        try:
            # Decode the refresh token
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            return None

        if payload.get("token_type") != "refresh":
            return None

        # Extract user ID
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None

        # Convert string user_id back to integer
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            return None

        user = UserService.get_user_by_id(db, user_id=user_id)
        return user


    @classmethod
    async def get_current_user(cls, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """ Gets the current user from the access token """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise credentials_exception

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception

        # Convert string user_id back to integer
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception

        token_data = TokenPayload(sub=user_id)
        user = UserService.get_user_by_id(db, user_id=token_data.sub)
        if user is None:
            raise credentials_exception
            
        return user

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import Token, SigninRequest, RefreshTokenRequest
from app.schemas.user import User, UserCreate, UserUpdate, PasswordChangeRequest
from app.services.user_service import UserService
from app.services.auth_service import AuthService

router = APIRouter()

@router.post("/signup/", response_model=User)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    try:
        user = UserService.create_user(db=db, user_in=user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return user


@router.post("/access_token/", response_model=Token)
def get_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """ Get an access token using username and password """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens using AuthService
    tokens = AuthService.create_user_tokens(user.id)
    return tokens


@router.post("/access_token_json/", response_model=Token)
def get_access_token_json(signin_data: SigninRequest, db: Session = Depends(get_db)):
    """ Get access token using JSON instead of form data """
    user = AuthService.authenticate_user(db, signin_data.username, signin_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens using AuthService
    tokens = AuthService.create_user_tokens(user.id)
    return tokens


@router.post("/refresh_token/", response_model=Token)
def refresh_access_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """ Get a new access token using a refresh token """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Validate refresh token and get user
    user = AuthService.validate_refresh_token(db, refresh_request.refresh_token)
    if user is None:
        raise credentials_exception

    # Create new tokens using AuthService
    tokens = AuthService.create_user_tokens(user.id)
    return tokens


@router.get("/user/", response_model=User)
def get_current_user(current_user: User = Depends(AuthService.get_current_user)):
    return current_user


@router.put("/user/", response_model=User)
def update_user(
    user_update: UserUpdate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = UserService.update_user(db=db, user_id=current_user.id, user_in=user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user


@router.put("/user/password/", response_model=User)
def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        updated_user = UserService.change_password(
            db=db,
            user_id=current_user.id,
            current_password=password_change.current_password,
            new_password=password_change.new_password,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return updated_user

from enum import Enum
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services.base_service import BaseService
from app.services.auth_utils import get_password_hash, verify_password


class UserService(BaseService[User]):
    model = User

    @classmethod
    def get_user_by_email(cls, db: Session, email: str) -> User | None:
        return cls.get_base_query(db).filter(User.email == email).first()

    @classmethod
    def get_user_by_username(cls, db: Session, username: str) -> User | None:
        return cls.get_base_query(db).filter(User.username == username).first()

    @classmethod
    def get_user_by_id(cls, db: Session, user_id: int) -> User | None:
        return cls.get_base_query(db).filter(User.id == user_id).first()

    @classmethod
    def create_user(cls, db: Session, user_in: UserCreate) -> User:
        # Check if user with this email or username already exists
        if cls.get_user_by_email(db, user_in.email):
            raise ValueError("Email already registered")

        if cls.get_user_by_username(db, user_in.username):
            raise ValueError("Username already taken")

        # Create new user
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(db_user)
        db.commit()

        db.refresh(db_user)
        return db_user

    @classmethod
    def update_user(cls, db: Session, user_id: int, user_in: UserUpdate) -> User | None:
        db_user = cls.get_user_by_id(db, user_id)
        if not db_user:
            return None

        update_data = user_in.model_dump(exclude_unset=True)
        for field, new_value in update_data.items():
            if isinstance(new_value, Enum):
                new_value = new_value.value
            setattr(db_user, field, new_value)
        db.commit()

        db.refresh(db_user)
        return db_user

    @classmethod
    def change_password(cls, db: Session, user_id: int, current_password: str, new_password: str) -> User | None:
        user = cls.get_user_by_id(db, user_id)
        if not user:
            return None

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            # Do not change anything if verification fails
            raise ValueError("Incorrect current password")

        # Update to new password
        user.hashed_password = get_password_hash(new_password)
        db.commit()

        db.refresh(user)
        return user

from typing import Generic, TypeVar

from sqlalchemy.orm import Session, Query

from app.models.base import BaseModel


T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    model: type[T]

    @classmethod
    def get_base_query(cls, db: Session) -> Query:
        return db.query(cls.model).filter(cls.model.is_deleted.is_(False))

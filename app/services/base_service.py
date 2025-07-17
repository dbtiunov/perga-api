from typing import Type, Generic, TypeVar

from sqlalchemy.orm import Session, Query

from app.models.base import BaseModel


T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    model: Type[T]

    @classmethod
    def get_base_query(cls, db: Session) -> Query:
        return db.query(cls.model).filter(cls.model.is_archived.is_(False))

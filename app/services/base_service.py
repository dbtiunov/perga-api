import logging
from sqlalchemy.orm import Session, Query
from sqlalchemy.exc import IntegrityError
from typing import Generic, TypeVar

from app.models.base import BaseModel


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T]):
    model: type[T]

    @classmethod
    def get_base_query(cls, db: Session) -> Query:
        return db.query(cls.model).filter(cls.model.is_deleted.is_(False))

    @classmethod
    def get_or_create(cls, db: Session, defaults: dict | None = None, **kwargs) -> tuple[T, bool]:
        instance = cls.get_base_query(db).filter_by(**kwargs).first()
        if instance:
            return instance, False

        params = {k: v for k, v in kwargs.items()}
        params.update(defaults or {})
        instance = cls.model(**params)
        db.add(instance)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            instance = cls.get_base_query(db).filter_by(**kwargs).first()
            return instance, False

        db.refresh(instance)
        return instance, True

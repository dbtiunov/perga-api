from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, Boolean

from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_dt = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_dt = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    is_deleted = Column(Boolean, default=False)
    deleted_dt = Column(DateTime(timezone=True), nullable=True, default=None)

    def mark_as_deleted(self):
        self.is_deleted = True
        self.deleted_dt = datetime.now(timezone.utc)

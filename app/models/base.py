from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, Boolean

from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_dt = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    is_archived = Column(Boolean, default=False)
    archived_dt = Column(DateTime, nullable=True, default=None)

    def archive(self):
        self.is_archived = True
        self.archived_dt = datetime.now(timezone.utc)

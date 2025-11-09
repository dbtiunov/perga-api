from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app import const
from app.models.base import BaseModel


__all__ = (
    'User',
)


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String(length=64), unique=True, index=True, nullable=False)
    email = Column(String(length=64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(length=128), nullable=False)
    is_active = Column(Boolean, default=True)
    week_start_day = Column(String(length=32), default=const.WeekStartDay.SUNDAY, nullable=False)

    # Relationships
    planner_agendas = relationship("PlannerAgenda", back_populates="user")
    planner_day_items = relationship("PlannerDayItem", back_populates="user")
    planner_agenda_items = relationship("PlannerAgendaItem", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email}, is_active={self.is_active})>"

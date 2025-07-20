from sqlalchemy import Column, String, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.choices import PlannerItemState, PlannerAgendaType


__all__ = (
    'PlannerAgenda',
    'PlannerAgendaItem',
    'PlannerDayItem',
)


class PlannerAgenda(BaseModel):
    __tablename__ = "planner_agendas"
    __table_args__ = (
        UniqueConstraint('user_id', 'agenda_type', 'name',  name='uix_user_agenda_type_name'),
    )

    name = Column(String(length=64), nullable=False)
    index = Column(Integer, default=0)
    agenda_type = Column(String(length=32), nullable=False, default=PlannerAgendaType.CUSTOM.value)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="planner_agendas")
    items = relationship("PlannerAgendaItem", back_populates="agenda")

    def __repr__(self):
        return f"<PlannerAgenda(id={self.id}, type={self.agenda_type}, name={self.name})>"


class BasePlannerItem(BaseModel):
    __abstract__ = True

    text = Column(String(length=64))
    index = Column(Integer, default=0)
    state = Column(String(length=32), nullable=False, default=PlannerItemState.TODO.value)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)


class PlannerDayItem(BasePlannerItem):
    __tablename__ = "planner_day_items"

    day = Column(Date, index=True)

    # Relationships
    user = relationship("User", back_populates="planner_day_items")

    def __repr__(self):
        return f"<PlannerDayItem(id={self.id}, day={self.day}, state={self.state})>"


class PlannerAgendaItem(BasePlannerItem):
    __tablename__ = "planner_agenda_items"

    agenda_id = Column(Integer, ForeignKey("planner_agendas.id"), nullable=False)

    # Relationships
    agenda = relationship("PlannerAgenda", back_populates="items")
    user = relationship("User", back_populates="planner_agenda_items")

    def __repr__(self):
        return f"<PlannerAgendaItem(id={self.id}, agenda_id={self.agenda_id}, state={self.state})>"

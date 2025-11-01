from datetime import datetime
from pydantic import BaseModel

from app.models.choices import PlannerItemState, PlannerAgendaType
from app.schemas.planner_day import BasePlannerItemBase


class PlannerAgendaCreate(BaseModel):
    agenda_type: PlannerAgendaType
    name: str
    index: int | None = None

    class Config:
        use_enum_values = True


class PlannerAgendaUpdate(BaseModel):
    name: str | None = None
    index: int | None = None

    class Config:
        use_enum_values = True


class PlannerAgenda(BaseModel):
    id: int
    agenda_type: str
    name: str
    index: int
    todo_items_cnt: int = 0
    completed_items_cnt: int = 0

    class Config:
        from_attributes = True


# Agenda Item schemas
class PlannerAgendaItemBase(BasePlannerItemBase):
    agenda_id: int


class PlannerAgendaItemCreate(BaseModel):
    agenda_id: int
    text: str


class PlannerAgendaItemUpdate(BaseModel):
    agenda_id: int | None = None
    text: str | None = None
    state: PlannerItemState | None = None


class PlannerAgendaItemInDBBase(PlannerAgendaItemBase):
    id: int
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True


class PlannerAgendaItem(PlannerAgendaItemBase):
    id: int


class ReorderAgendaItemsRequest(BaseModel):
    ordered_item_ids: list[int]


class ReorderAgendasRequest(BaseModel):
    ordered_agenda_ids: list[int]

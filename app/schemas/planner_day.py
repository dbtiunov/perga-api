from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel

from app.models.choices import PlannerItemState


# Base schemas for planner items
class BasePlannerItemBase(BaseModel):
    text: str
    index: int
    state: PlannerItemState
    user_id: int

    class Config:
        use_enum_values = True


class PlannerDayItemBase(BasePlannerItemBase):
    day: date


class PlannerDayItemCreate(BaseModel):
    day: date
    text: str


class PlannerDayItemUpdate(BaseModel):
    day: Optional[date] = None
    text: Optional[str] = None
    state: Optional[PlannerItemState] = None


# class PlannerDayItemInDBBase(PlannerDayItemBase):
#     id: int
#     created_dt: datetime
#     updated_dt: datetime
#
#     class Config:
#         from_attributes = True


class PlannerDayItem(BaseModel):
    id: int
    day: date
    text: str
    state: PlannerItemState


class ReorderDayItemsRequest(BaseModel):
    ordered_item_ids: List[int]


class CopyDayItemRequest(BaseModel):
    day: date


class SnoozeDayItemRequest(BaseModel):
    day: date

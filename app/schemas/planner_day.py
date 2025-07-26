from datetime import date
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
    day: date | None = None
    text: str | None = None
    state: PlannerItemState | None = None


class PlannerDayItem(BaseModel):
    id: int
    day: date
    text: str
    state: PlannerItemState


class ReorderDayItemsRequest(BaseModel):
    ordered_item_ids: int | None


class CopyDayItemRequest(BaseModel):
    day: date


class SnoozeDayItemRequest(BaseModel):
    day: date

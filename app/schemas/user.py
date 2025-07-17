from typing import Optional
from pydantic import BaseModel

from app.models.choices import WeekStartDay


class User(BaseModel):
    username: str
    email: str
    week_start_day: WeekStartDay

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    week_start_day: WeekStartDay = WeekStartDay.SUNDAY


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    week_start_day: Optional[WeekStartDay] = None

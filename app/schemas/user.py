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
    username: str | None = None
    email: str | None = None
    week_start_day: WeekStartDay | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

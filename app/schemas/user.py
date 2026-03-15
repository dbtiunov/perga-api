from pydantic import BaseModel

from app.const.planner import WeekStartDay


class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    week_start_day: WeekStartDay

    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    username: str
    email: str
    password: str
    week_start_day: WeekStartDay = WeekStartDay.SUNDAY


class UserUpdateSchema(BaseModel):
    username: str | None = None
    email: str | None = None
    week_start_day: WeekStartDay | None = None


class PasswordChangeSchema(BaseModel):
    current_password: str
    new_password: str

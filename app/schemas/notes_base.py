from datetime import datetime
from pydantic import BaseModel


class NoteCreateSchema(BaseModel):
    title: str | None = None
    body: str
    index: int | None = None
    folder_id: int | None = None


class NoteUpdateSchema(BaseModel):
    title: str | None = None
    body: str | None = None
    index: int | None = None
    folder_id: int | None = None


class NoteSchema(BaseModel):
    id: int
    title: str | None
    body: str
    index: int
    folder_id: int | None
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True

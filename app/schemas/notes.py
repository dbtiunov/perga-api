from datetime import datetime
from pydantic import BaseModel


class NoteCreateSchema(BaseModel):
    folder_id: int | None = None
    title: str | None = None
    body: str | None = None
    index: int | None = None


class NoteUpdateSchema(BaseModel):
    folder_id: int | None = None
    title: str | None = None
    body: str | None = None
    index: int | None = None


# NoteSchema without body to reduce get_folders response size
class NoteMetaSchema(BaseModel):
    id: int
    folder_id: int
    title: str | None
    index: int
    updated_dt: datetime

    class Config:
        from_attributes = True


class NoteSchema(NoteMetaSchema):
    body: str | None

    class Config:
        from_attributes = True

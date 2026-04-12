import datetime as dt
from pydantic import BaseModel


class NoteCreateSchema(BaseModel):
    folder_id: int
    title: str = ''
    body: str = ''


class NoteUpdateSchema(BaseModel):
    folder_id: int = None
    title: str = None
    body: str = None


# NoteSchema without body to reduce get_folders response size
class NoteMetaSchema(BaseModel):
    id: int
    folder_id: int
    title: str
    updated_dt: dt.datetime

    class Config:
        from_attributes = True


class NoteSchema(NoteMetaSchema):
    body: str

    class Config:
        from_attributes = True

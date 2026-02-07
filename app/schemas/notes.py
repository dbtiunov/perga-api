from datetime import datetime
from pydantic import BaseModel


# Notes Folder Schemas
class NotesFolderCreateSchema(BaseModel):
    name: str
    index: int | None = None
    parent_id: int | None = None


class NotesFolderUpdateSchema(BaseModel):
    name: str | None = None
    index: int | None = None
    parent_id: int | None = None


class NotesFolderSchema(BaseModel):
    id: int
    name: str
    index: int
    parent_id: int | None = None
    folder_type: str

    class Config:
        from_attributes = True


# Note Schemas
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


class NotesFolderTreeSchema(NotesFolderSchema):
    subfolders: list['NotesFolderTreeSchema'] = []

    class Config:
        from_attributes = True


class NotesFolderTreeWithNotesSchema(NotesFolderTreeSchema):
    notes: list[NoteSchema] = []
    subfolders: list['NotesFolderTreeWithNotesSchema'] = []

    class Config:
        from_attributes = True

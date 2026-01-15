from datetime import datetime
from pydantic import BaseModel


# Notes Folder Schemas
class NotesFolderCreate(BaseModel):
    name: str
    index: int | None = None


class NotesFolderUpdate(BaseModel):
    name: str | None = None
    index: int | None = None


class NotesFolder(BaseModel):
    id: int
    name: str
    index: int

    class Config:
        from_attributes = True


# Note Schemas
class NoteCreate(BaseModel):
    title: str | None = None
    body: str
    index: int | None = None
    folder_id: int | None = None


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    index: int | None = None
    folder_id: int | None = None


class Note(BaseModel):
    id: int
    title: str | None
    body: str
    index: int
    folder_id: int | None
    created_dt: datetime
    updated_dt: datetime

    class Config:
        from_attributes = True

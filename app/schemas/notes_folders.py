from pydantic import BaseModel
from .notes_base import NoteSchema


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


class NotesFolderTreeSchema(NotesFolderSchema):
    subfolders: list['NotesFolderTreeSchema'] = []

    class Config:
        from_attributes = True


class NotesFolderTreeWithNotesSchema(NotesFolderTreeSchema):
    notes: list[NoteSchema] = []
    subfolders: list['NotesFolderTreeWithNotesSchema'] = []

    class Config:
        from_attributes = True


class NotesFoldersResponseSchema(BaseModel):
    root_folder: NotesFolderTreeSchema | NotesFolderTreeWithNotesSchema
    trash_folder: NotesFolderTreeSchema | NotesFolderTreeWithNotesSchema

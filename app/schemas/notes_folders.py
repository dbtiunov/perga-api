from pydantic import BaseModel

from app.schemas.notes import NoteSchema


class NotesFolderCreateSchema(BaseModel):
    parent_id: int | None = None
    name: str


class NotesFolderUpdateSchema(BaseModel):
    parent_id: int | None = None
    name: str | None = None
    index: int | None = None


class NotesFolderSchema(BaseModel):
    parent_id: int | None = None
    id: int
    folder_type: str
    name: str
    index: int

    class Config:
        from_attributes = True


class NotesFolderRespsonseSchema(NotesFolderSchema):
    notes: list[NoteSchema] = []
    subfolders: list['NotesFolderRespsonseSchema'] = []

    class Config:
        from_attributes = True


class NotesFoldersResponseSchema(BaseModel):
    root_folder: NotesFolderRespsonseSchema
    trash_folder: NotesFolderRespsonseSchema

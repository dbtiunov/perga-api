from pydantic import BaseModel, field_validator

from app.schemas.notes import NoteMetaSchema


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
    notes: list[NoteMetaSchema] = []
    subfolders: list['NotesFolderRespsonseSchema'] = []

    @field_validator('notes', mode='after')
    @classmethod
    def sort_notes(cls, v: list[NoteMetaSchema]) -> list[NoteMetaSchema]:
        # Sort notes by updated_dt desc.
        return sorted(v, key=lambda x: x.updated_dt, reverse=True)

    class Config:
        from_attributes = True


class NotesFoldersResponseSchema(BaseModel):
    root_folder: NotesFolderRespsonseSchema
    trash_folder: NotesFolderRespsonseSchema

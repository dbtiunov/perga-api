from pydantic import BaseModel


class NoteCreateSchema(BaseModel):
    folder_id: int
    title: str | None = None
    body: str | None = None
    index: int | None = None


class NoteUpdateSchema(BaseModel):
    folder_id: int | None = None
    title: str | None = None
    body: str | None = None
    index: int | None = None


class NoteSchema(BaseModel):
    id: int
    folder_id: int
    title: str | None
    body: str | None
    index: int

    class Config:
        from_attributes = True

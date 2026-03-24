from pydantic import BaseModel


class NotesImportResponseSchema(BaseModel):
    imported_count: int

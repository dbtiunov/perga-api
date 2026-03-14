from pydantic import BaseModel

from app.const.notes import ExportType, ExportTarget


class NotesExportRequestSchema(BaseModel):
    export_type: ExportType
    export_target: ExportTarget
    export_target_id: int | None = None  # None in case of all_notes

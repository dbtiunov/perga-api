from fastapi import Depends, HTTPException, APIRouter
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.const.notes import ExportTarget, EXPORT_MEDIA_TYPE_MAP
from app.core.database import get_db
from app.schemas.notes_export import NotesExportRequestSchema
from app.schemas.user import UserSchema
from app.services.auth_service import AuthService
from app.services.notes_export_service import NotesExportService

router = APIRouter()


@router.post('/')
def notes_export(
    request_data: NotesExportRequestSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    export_type = request_data.export_type
    if not export_type:
        return HTTPException(status_code=400, detail='Export type is required')
    media_type = EXPORT_MEDIA_TYPE_MAP.get(export_type)

    export_target = request_data.export_target
    export_target_id = request_data.export_target_id
    if export_target == ExportTarget.SINGLE_NOTE and export_target_id:
        content, filename = NotesExportService.export_single_note(
            db,
            user_id=current_user.id,
            note_id=export_target_id,
            export_type=export_type
        )
        if not content:
            raise HTTPException(status_code=404, detail='Note not found')

        return Response(
            content=content,
            media_type=media_type,
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    elif export_target == ExportTarget.FOLDER_NOTES and export_target_id:
        zip_buffer, filename = NotesExportService.export_folder(
            db,
            user_id=current_user.id,
            folder_id=export_target_id,
            export_type=export_type
        )
        if not zip_buffer:
            raise HTTPException(status_code=404, detail='Folder not found')
    elif export_target == ExportTarget.ALL_NOTES:
        zip_buffer, filename = NotesExportService.export_all_notes(
            db, user_id=current_user.id, export_type=request_data.export_type
        )
    else:
        raise HTTPException(status_code=400, detail='One of note_id, notes_folder_id or all must be provided')

    return StreamingResponse(
        zip_buffer,
        media_type='application/x-zip-compressed',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

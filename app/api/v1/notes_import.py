from fastapi import Depends, HTTPException, APIRouter, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.const.notes import IMPORT_SIZE_LIMIT, IMPORT_SIZE_LIMIT_MB
from app.core.database import get_db
from app.models.user import User
from app.schemas.notes_import import NotesImportResponseSchema
from app.services.auth_service import AuthService
from app.services.notes_folders_service import NotesFolderService
from app.services.notes_import_service import NotesImportService

router = APIRouter()


@router.post('/', response_model=NotesImportResponseSchema)
async def import_notes(
    files: list[UploadFile] = File(...),
    folder_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    # validate files size based on the Content-Length header if it exists
    total_size = 0
    for file in files:
        total_size += file.size or 0
    if total_size > IMPORT_SIZE_LIMIT:
        raise HTTPException(
            status_code=413,
            detail=f'Import upload size is too large. Max total size is {IMPORT_SIZE_LIMIT_MB}MB'
        )

    # validate provided folder_id or create import folder
    if folder_id:
        target_folder = NotesFolderService.get_folder(db, folder_id, current_user.id)
        if not target_folder:
            raise HTTPException(status_code=404, detail='Folder not found')
    else:
        target_folder = NotesFolderService.create_import_folder(db, current_user.id)
    folder_id = target_folder.id

    # process files
    imported_notes = []
    total_content_size = 0
    for file in files:
        content = await file.read()
        total_content_size += len(content)

        # validate actual content size
        if total_content_size > IMPORT_SIZE_LIMIT:
             raise HTTPException(
                status_code=413,
                detail=f'Import content size is too large. Max total size is {IMPORT_SIZE_LIMIT_MB}MB'
            )

        filename = file.filename
        
        if filename.lower().endswith('.zip'):
            notes = NotesImportService.import_zip(
                db,
                user_id=current_user.id,
                zip_content=content,
                folder_id=folder_id
            )
            imported_notes.extend(notes)
        else:
            note = NotesImportService.import_file(
                db,
                user_id=current_user.id,
                filename=filename,
                content=content,
                folder_id=folder_id
            )
            if not note:
                # skip files that cannot be imported
                continue
            imported_notes.append(note)

    if not imported_notes and files:
        raise HTTPException(status_code=400, detail='No valid notes found in the uploaded files.')
        
    return {
        'imported_count': len(imported_notes),
    }

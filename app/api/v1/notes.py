from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.notes import NoteSchema, NoteCreateSchema, NoteUpdateSchema
from app.schemas.user import UserSchema
from app.services.auth_service import AuthService
from app.services.notes_service import NoteService

router = APIRouter()


@router.post("/", response_model=NoteSchema)
def create_note(
    request_data: NoteCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.create_note(db, user_id=current_user.id, create_data=request_data)
    return note


@router.get("/{note_id}/", response_model=NoteSchema)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.get_note(db, note_id=note_id, user_id=current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.patch("/{note_id}/", response_model=NoteSchema)
def update_note(
    note_id: int,
    request_data: NoteUpdateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.update_note(db, note_id=note_id, user_id=current_user.id, update_data=request_data)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

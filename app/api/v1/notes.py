from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.notes import (
    NoteSchema,
    NoteCreateSchema,
    NoteUpdateSchema,
)
from app.schemas.user import UserSchema
from app.services.auth_service import AuthService
from app.services.notes_service import NoteService

router = APIRouter()


@router.get("/", response_model=list[NoteSchema])
def list_notes(
    folder_id: int | None = Query(None, description="Filter notes by folder_id"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    notes = NoteService.list_notes(db, user_id=current_user.id, folder_id=folder_id)
    return notes


@router.post("/", response_model=NoteSchema)
def create_note(
    note_in: NoteCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.create_note(db, user_id=current_user.id, note_in=note_in)
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
    note_in: NoteUpdateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.update_note(db, note_id=note_id, user_id=current_user.id, note_in=note_in)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/{note_id}/move-to-trash/", response_model=NoteSchema)
def move_note_to_trash(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    note = NoteService.move_to_trash(db, note_id=note_id, user_id=current_user.id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

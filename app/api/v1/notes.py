from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.note import (
    NoteSchema as NoteSchema,
    NoteCreateSchema,
    NoteUpdateSchema,
    NotesFolderSchema as NotesFolderSchema,
    NotesFolderCreateSchema,
    NotesFolderUpdateSchema,
    NotesFolderTreeSchema,
    NotesFolderTreeWithNotesSchema,
)
from app.schemas.user import UserSchema
from app.services.auth_service import AuthService
from app.services.note_service import NoteService, NotesFolderService

router = APIRouter()

# Notes Folders endpoints
@router.get("/folders/", response_model=list[NotesFolderSchema])
def list_notes_folders(
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    return NotesFolderService.list_folders(db, user_id=current_user.id)


@router.get("/folders/tree/", response_model=list[NotesFolderTreeSchema | NotesFolderTreeWithNotesSchema])
def get_folders_tree(
    include_notes: bool = Query(False, description="Include notes in the tree"),
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    return NotesFolderService.get_folders_tree(db, user_id=current_user.id)


@router.post("/folders/", response_model=NotesFolderSchema)
def create_notes_folder(
    folder_in: NotesFolderCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    return NotesFolderService.create_folder(db, user_id=current_user.id, folder_in=folder_in)


@router.patch("/folders/{folder_id}/", response_model=NotesFolderSchema)
def update_notes_folder(
    folder_id: int,
    folder_in: NotesFolderUpdateSchema,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    folder = NotesFolderService.update_folder(db, folder_id=folder_id, user_id=current_user.id, folder_in=folder_in)
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.delete("/folders/{folder_id}/", response_model=dict)
def delete_notes_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    success = NotesFolderService.delete_folder(db, folder_id=folder_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Folder not found")
    return {"detail": "Folder deleted"}


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


@router.delete("/{note_id}/", response_model=dict)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: UserSchema = Depends(AuthService.get_current_user)
):
    success = NoteService.delete_note(db, note_id=note_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"detail": "Note deleted"}

from sqlalchemy.orm import Session

from app.models.notes import Note
from app.schemas.notes import NoteCreateSchema, NoteUpdateSchema
from app.services.base_service import BaseService
from app.services.notes_folders_service import NotesFolderService


class NoteService(BaseService[Note]):
    model = Note

    @classmethod
    def get_note(cls, db: Session, note_id: int, user_id: int) -> Note | None:
        return cls.get_base_query(db).filter(Note.user_id == user_id, Note.id == note_id).first()

    @classmethod
    def get_new_note_index(cls, db: Session, user_id: int, folder_id: int | None = None) -> int:
        query = cls.get_base_query(db).filter(Note.user_id == user_id, Note.folder_id == folder_id)
        max_index_note = query.order_by(Note.index.desc()).first()
        return (max_index_note.index + 1) if max_index_note else 0

    @classmethod
    def create_note(cls, db: Session, user_id: int, create_data: NoteCreateSchema) -> Note:
        data = create_data.model_dump()
        if data.get('folder_id') is None:
            root_folder = NotesFolderService.get_root_folder(db, user_id)
            data['folder_id'] = root_folder.id
            
        if data.get('index') is None:
            data['index'] = cls.get_new_note_index(db, user_id, folder_id=data.get('folder_id'))
        db_note = Note(user_id=user_id, **data)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note

    @classmethod
    def update_note(cls, db: Session, note_id: int, user_id: int, update_data: NoteUpdateSchema) -> Note | None:
        db_note = cls.get_note(db, note_id, user_id)
        if not db_note:
            return None
        update_data = update_data.model_dump(exclude_unset=True)
        
        # If folder_id is changed and index is not provided, move to the end of the new folder
        if 'folder_id' in update_data and db_note.folder_id != update_data['folder_id'] and 'index' not in update_data:
            update_data['index'] = cls.get_new_note_index(db, user_id, folder_id=update_data['folder_id'])
            
        for field, value in update_data.items():
            setattr(db_note, field, value)
        db.commit()

        db.refresh(db_note)
        return db_note

    @classmethod
    def delete_note(cls, db: Session, note_id: int, user_id: int) -> bool:
        db_note = cls.get_note(db, note_id, user_id)
        if not db_note:
            return False
        db_note.mark_as_deleted()
        db.commit()
        return True

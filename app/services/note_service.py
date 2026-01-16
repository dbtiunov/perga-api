from sqlalchemy.orm import Session

from app.models.note import Note, NotesFolder
from app.services.base_service import BaseService
from app.schemas.note import NoteCreateSchema, NoteUpdateSchema, NotesFolderCreateSchema, NotesFolderUpdateSchema


class NoteService(BaseService[Note]):
    model = Note

    @classmethod
    def list_notes(cls, db: Session, user_id: int, folder_id: int | None = None) -> list[Note]:
        query = cls.get_base_query(db).filter(Note.user_id == user_id)
        if folder_id is not None:
            query = query.filter(Note.folder_id == folder_id)
        return query.order_by(Note.updated_dt.desc()).all()

    @classmethod
    def get_note(cls, db: Session, note_id: int, user_id: int) -> Note | None:
        return cls.get_base_query(db).filter(Note.user_id == user_id, Note.id == note_id).first()

    @classmethod
    def create_note(cls, db: Session, user_id: int, note_in: NoteCreateSchema) -> Note:
        db_note = Note(user_id=user_id, **note_in.model_dump())
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note

    @classmethod
    def update_note(cls, db: Session, note_id: int, user_id: int, note_in: NoteUpdateSchema) -> Note | None:
        db_note = cls.get_note(db, note_id, user_id)
        if not db_note:
            return None
        update_data = note_in.model_dump(exclude_unset=True)
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


class NotesFolderService(BaseService[NotesFolder]):
    model = NotesFolder

    @classmethod
    def list_folders(cls, db: Session, user_id: int) -> list[NotesFolder]:
        return cls.get_base_query(db).filter(NotesFolder.user_id == user_id).order_by(NotesFolder.index).all()

    @classmethod
    def get_folder(cls, db: Session, folder_id: int, user_id: int) -> NotesFolder | None:
        return cls.get_base_query(db).filter(NotesFolder.user_id == user_id, NotesFolder.id == folder_id).first()

    @classmethod
    def get_new_folder_index(cls, db: Session, user_id: int) -> int:
        query = cls.get_base_query(db).filter(NotesFolder.user_id == user_id)
        max_folder = query.order_by(NotesFolder.index.desc()).first()
        return (max_folder.index + 1) if max_folder else 0

    @classmethod
    def create_folder(cls, db: Session, user_id: int, folder_in: NotesFolderCreateSchema) -> NotesFolder:
        data = folder_in.model_dump()
        if data.get('index') is None:
            data['index'] = cls.get_new_folder_index(db, user_id)
        db_folder = NotesFolder(user_id=user_id, **data)
        db.add(db_folder)
        db.commit()
        db.refresh(db_folder)
        return db_folder

    @classmethod
    def update_folder(cls, db: Session, folder_id: int, user_id: int, folder_in: NotesFolderUpdateSchema) -> NotesFolder | None:
        db_folder = cls.get_folder(db, folder_id, user_id)
        if not db_folder:
            return None
        update_data = folder_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_folder, field, value)
        db.commit()
        db.refresh(db_folder)
        return db_folder

    @classmethod
    def delete_folder(cls, db: Session, folder_id: int, user_id: int) -> bool:
        db_folder = cls.get_folder(db, folder_id, user_id)
        if not db_folder:
            return False
        db_folder.mark_as_deleted()
        db.commit()
        return True

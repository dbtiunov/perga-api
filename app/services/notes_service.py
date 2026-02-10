from sqlalchemy.orm import Session

from app.const.notes import NotesFolderType
from app.models.notes import Note, NotesFolder
from app.services.base_service import BaseService
from app.schemas.notes import NoteCreateSchema, NoteUpdateSchema, NotesFolderCreateSchema, NotesFolderUpdateSchema


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

    @classmethod
    def move_to_trash(cls, db: Session, note_id: int, user_id: int) -> Note | None:
        db_note = cls.get_note(db, note_id, user_id)
        if not db_note:
            return None

        trash_folder = NotesFolderService.get_trash_folder(db, user_id)
        db_note.folder_id = trash_folder.id
        db.commit()
        db.refresh(db_note)
        return db_note


class NotesFolderService(BaseService[NotesFolder]):
    model = NotesFolder

    @classmethod
    def list_folders(cls, db: Session, user_id: int) -> list[NotesFolder]:
        return cls.get_base_query(db).filter(NotesFolder.user_id == user_id).order_by(NotesFolder.index).all()

    @classmethod
    def get_folder(cls, db: Session, folder_id: int, user_id: int) -> NotesFolder | None:
        return cls.get_base_query(db).filter(NotesFolder.user_id == user_id, NotesFolder.id == folder_id).first()

    @classmethod
    def get_new_folder_index(cls, db: Session, user_id: int, parent_id: int | None = None) -> int:
        query = cls.get_base_query(db).filter(NotesFolder.user_id == user_id, NotesFolder.parent_id == parent_id)
        max_folder = query.order_by(NotesFolder.index.desc()).first()
        return (max_folder.index + 1) if max_folder else 0

    @classmethod
    def create_folder(cls, db: Session, user_id: int, folder_in: NotesFolderCreateSchema) -> NotesFolder:
        data = folder_in.model_dump()
        if data.get('index') is None:
            data['index'] = cls.get_new_folder_index(db, user_id, parent_id=data.get('parent_id'))
        db_folder = NotesFolder(
            user_id=user_id,
            folder_type=NotesFolderType.REGULAR,
            **data
        )
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

    @classmethod
    def get_trash_folder(cls, db: Session, user_id: int) -> NotesFolder:
        trash_folder = cls.get_base_query(db).filter(
            NotesFolder.user_id == user_id,
            NotesFolder.folder_type == NotesFolderType.TRASH
        ).first()
        if not trash_folder:
            trash_folder = NotesFolder(
                user_id=user_id,
                name="Trash",
                folder_type=NotesFolderType.TRASH,
                index=0
            )
            db.add(trash_folder)
            db.commit()
            db.refresh(trash_folder)
        return trash_folder

    @classmethod
    def get_folders_tree(cls, db: Session, user_id: int) -> list[NotesFolder]:
        trash_folder = cls.get_trash_folder(db, user_id)
        
        all_folders = cls.get_base_query(db).filter(
            NotesFolder.user_id == user_id,
            NotesFolder.folder_type == NotesFolderType.REGULAR
        ).order_by(NotesFolder.index).all()
        
        root_folders = [f for f in all_folders if f.parent_id is None]
        return root_folders + [trash_folder]

    @classmethod
    def move_to_trash(cls, db: Session, folder_id: int, user_id: int) -> NotesFolder | None:
        db_folder = cls.get_folder(db, folder_id, user_id)
        if not db_folder:
            return None
        
        trash_folder = cls.get_trash_folder(db, user_id)
        db_folder.parent_id = trash_folder.id
        db.commit()
        db.refresh(db_folder)
        return db_folder

    @classmethod
    def empty_trash(cls, db: Session, user_id: int) -> None:
        trash_folder = cls.get_trash_folder(db, user_id)
        
        def mark_children_as_deleted(folder: NotesFolder):
            """ Recursively mark subfolders and notes as deleted """
            # Mark all notes in this folder as deleted
            for note in folder.notes:
                if not note.is_deleted:
                    note.mark_as_deleted()
            
            # Recursively mark subfolders and their contents as deleted
            for subfolder in folder.subfolders:
                if not subfolder.is_deleted:
                    subfolder.mark_as_deleted()
                mark_children_as_deleted(subfolder)

        mark_children_as_deleted(trash_folder)
        db.commit()

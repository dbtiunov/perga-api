from sqlalchemy.orm import Session

from app.const.notes import NotesFolderType
from app.models.notes import NotesFolder
from app.services.base_service import BaseService
from app.schemas.notes_folders import NotesFolderCreateSchema, NotesFolderUpdateSchema


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
        max_index_folder = query.order_by(NotesFolder.index.desc()).first()
        return (max_index_folder.index + 1) if max_index_folder else 0

    @classmethod
    def create_folder(cls, db: Session, user_id: int, request_data: NotesFolderCreateSchema) -> NotesFolder:
        data = request_data.model_dump()
        if data.get('parent_id') is None:
            root_folder = cls.get_root_folder(db, user_id)
            data['parent_id'] = root_folder.id
            
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
    def update_folder(cls, db: Session, folder_id: int, user_id: int, request_data: NotesFolderUpdateSchema) -> NotesFolder | None:
        db_folder = cls.get_folder(db, folder_id, user_id)
        if not db_folder:
            return None
        update_data = request_data.model_dump(exclude_unset=True)
        
        # If parent_id is changed and index is not provided, move to the end of the new parent
        if 'parent_id' in update_data and db_folder.parent_id != update_data['parent_id'] and 'index' not in update_data:
            update_data['index'] = cls.get_new_folder_index(db, user_id, parent_id=update_data['parent_id'])
            
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
                index=1
            )
            db.add(trash_folder)
            db.commit()
            db.refresh(trash_folder)
        return trash_folder

    @classmethod
    def get_root_folder(cls, db: Session, user_id: int) -> NotesFolder:
        root_folder = cls.get_base_query(db).filter(
            NotesFolder.user_id == user_id,
            NotesFolder.folder_type == NotesFolderType.ROOT
        ).first()
        if not root_folder:
            root_folder = NotesFolder(
                user_id=user_id,
                name="Root",
                folder_type=NotesFolderType.ROOT,
                index=0
            )
            db.add(root_folder)
            db.commit()
            db.refresh(root_folder)
        return root_folder

    @classmethod
    def get_folders(cls, db: Session, user_id: int) -> dict:
        root_folder = cls.get_root_folder(db, user_id)
        trash_folder = cls.get_trash_folder(db, user_id)
        return {
            "root_folder": root_folder,
            "trash_folder": trash_folder
        }

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

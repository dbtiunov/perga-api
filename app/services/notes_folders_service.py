from datetime import datetime
from sqlalchemy.orm import Session

from app.const.notes import NotesFolderType
from app.models.notes import NotesFolder
from app.schemas.notes_folders import NotesFolderCreateSchema, NotesFolderUpdateSchema
from app.services.base_service import BaseService


class NotesFolderService(BaseService[NotesFolder]):
    model = NotesFolder

    @classmethod
    def get_folder(cls, db: Session, folder_id: int, user_id: int) -> NotesFolder | None:
        return cls.get_base_query(db).filter(NotesFolder.user_id == user_id, NotesFolder.id == folder_id).first()

    @classmethod
    def create_folder(cls, db: Session, user_id: int, create_data: NotesFolderCreateSchema) -> NotesFolder:
        data = create_data.model_dump()
        if data.get('parent_id') is None:
            root_folder = cls.get_root_folder(db, user_id)
            data['parent_id'] = root_folder.id
            
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
    def update_folder(
        cls, db: Session, folder_id: int, user_id: int, update_data: NotesFolderUpdateSchema
    ) -> NotesFolder | None:
        db_folder = cls.get_folder(db, folder_id, user_id)
        if not db_folder:
            return None
        update_data = update_data.model_dump(exclude_unset=True)
        
        if 'parent_id' in update_data and update_data['parent_id'] is not None:
            new_parent_id = update_data['parent_id']
            if (
                new_parent_id == folder_id or
                    cls.is_subfolder_of(db, folder_id, new_parent_id, user_id)
            ):
                return None

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
    def get_root_folder(cls, db: Session, user_id: int) -> NotesFolder:
        instance, _ = cls.get_or_create(
            db,
            user_id=user_id,
            folder_type=NotesFolderType.ROOT,
            defaults={'name': 'Root'}
        )
        return instance

    @classmethod
    def get_trash_folder(cls, db: Session, user_id: int) -> NotesFolder:
        instance, _ = cls.get_or_create(
            db,
            user_id=user_id,
            folder_type=NotesFolderType.TRASH,
            defaults={'name': 'Trash'}
        )
        return instance

    @classmethod
    def get_folders(cls, db: Session, user_id: int) -> dict:
        root_folder = cls.get_root_folder(db, user_id)
        trash_folder = cls.get_trash_folder(db, user_id)
        return {
            'root_folder': root_folder,
            'trash_folder': trash_folder
        }

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

    @classmethod
    def is_subfolder_of(cls, db: Session, folder1_id: int, folder2_id: int, user_id: int) -> bool:
        """ Check if folder2_id is a subfolder of folder1_id """
        folder2 = cls.get_folder(db, folder2_id, user_id)
        while folder2 and folder2.parent_id:
            if folder2.parent_id == folder1_id:
                return True
            folder2 = folder2.parent
        return False

    @classmethod
    def create_import_folder(cls, db: Session, user_id: int) -> NotesFolder:
        """ Create a new folder for import with a unique name. """
        current_date = datetime.now().strftime('%Y-%m-%d')
        base_name = f'import_{current_date}'
        
        # fetch folders that start with base_name and get a unique name for the new folder
        existing_folders = cls.get_base_query(db).filter(
            NotesFolder.user_id == user_id,
            NotesFolder.name.startswith(base_name)
        ).all()
        existing_names = {f.name for f in existing_folders}
        
        folder_name = base_name
        index = 1
        while folder_name in existing_names:
            folder_name = f'{base_name}_{index}'
            index += 1
            
        root_folder = cls.get_root_folder(db, user_id)
        return cls.create_folder(
            db,
            user_id,
            NotesFolderCreateSchema(name=folder_name, parent_id=root_folder.id)
        )

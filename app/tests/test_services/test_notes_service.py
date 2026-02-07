from sqlalchemy.orm import Session

from app.services.notes_service import NoteService
from app.schemas.notes import NoteCreateSchema, NoteUpdateSchema
from app.models.notes import Note


class TestNoteService:
    def test_create_and_get_note(self, test_db: Session, test_user):
        create = NoteCreateSchema(title="My Note", body="Hello world")
        note = NoteService.create_note(test_db, user_id=test_user.id, note_in=create)

        assert note.id is not None
        assert note.title == "My Note"
        assert note.body == "Hello world"
        assert note.user_id == test_user.id

        fetched = NoteService.get_note(test_db, note_id=note.id, user_id=test_user.id)
        assert fetched is not None
        assert fetched.id == note.id

    def test_list_notes_scoped_by_user(self, test_db: Session, test_user):
        # Create a note for the test_user
        NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreateSchema(body="A"))
        # Create a note for another user
        other = Note(title="Other", body="B", user_id=test_user.id + 1)
        test_db.add(other)
        test_db.commit()

        notes = NoteService.list_notes(test_db, user_id=test_user.id)
        assert len(notes) == 1
        assert notes[0].user_id == test_user.id

    def test_update_note(self, test_db: Session, test_user):
        note = NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreateSchema(title=None, body="old"))
        updated = NoteService.update_note(
            test_db,
            note_id=note.id,
            user_id=test_user.id,
            note_in=NoteUpdateSchema(title="New Title", body="new")
        )
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.body == "new"

    def test_delete_note_soft(self, test_db: Session, test_user):
        note = NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreateSchema(body="to delete"))
        ok = NoteService.delete_note(test_db, note_id=note.id, user_id=test_user.id)
        assert ok is True

        # Should not appear in base query anymore
        found = NoteService.get_note(test_db, note_id=note.id, user_id=test_user.id)
        assert found is None


class TestNotesFolderService:
    def test_create_subfolder(self, test_db: Session, test_user):
        from app.services.notes_service import NotesFolderService
        from app.schemas.notes import NotesFolderCreateSchema

        # 1. Create a parent folder
        parent_create = NotesFolderCreateSchema(name="Parent Folder")
        parent = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=parent_create)
        
        assert parent.id is not None
        assert parent.name == "Parent Folder"
        
        # 2. Create a subfolder
        subfolder_create = NotesFolderCreateSchema(name="Subfolder", parent_id=parent.id)
        subfolder = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=subfolder_create)
        
        assert subfolder.id is not None
        assert subfolder.parent_id == parent.id
        
        # 3. Verify relationship
        test_db.refresh(parent)
        assert len(parent.subfolders) == 1
        assert parent.subfolders[0].id == subfolder.id
        assert subfolder.parent.id == parent.id

    def test_folder_index_scoped_by_parent(self, test_db: Session, test_user):
        from app.services.notes_service import NotesFolderService
        from app.schemas.notes import NotesFolderCreateSchema

        # Root folders
        f1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="F1"))
        f2 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="F2"))
        assert f1.index == 0
        assert f2.index == 1
        
        # Subfolders of f1
        sf1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="SF1", parent_id=f1.id))
        sf2 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="SF2", parent_id=f1.id))
        assert sf1.index == 0
        assert sf2.index == 1

    def test_get_folders_tree_includes_trash(self, test_db: Session, test_user):
        from app.services.notes_service import NotesFolderService
        from app.schemas.notes import NotesFolderCreateSchema
        from app.const.notes import NotesFolderType

        # Create a regular folder
        NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="Regular"))

        tree = NotesFolderService.get_folders_tree(test_db, user_id=test_user.id)
        
        # Should have Regular and Trash
        assert len(tree) == 2
        trash = next(f for f in tree if f.folder_type == NotesFolderType.TRASH)
        assert trash.name == "Trash"
        regular = next(f for f in tree if f.folder_type == NotesFolderType.REGULAR)
        assert regular.name == "Regular"

    def test_move_to_trash_service(self, test_db: Session, test_user):
        from app.services.notes_service import NotesFolderService
        from app.schemas.notes import NotesFolderCreateSchema
        from app.const.notes import NotesFolderType

        folder = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="To Trash"))
        NotesFolderService.move_to_trash(test_db, folder_id=folder.id, user_id=test_user.id)
        
        test_db.refresh(folder)
        trash_folder = NotesFolderService.get_trash_folder(test_db, user_id=test_user.id)
        assert folder.parent_id == trash_folder.id

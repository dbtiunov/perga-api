from sqlalchemy.orm import Session

from app.schemas.notes import NoteCreateSchema, NoteUpdateSchema
from app.services.notes_folders_service import NotesFolderService
from app.services.notes_service import NoteService


class TestNoteService:
    def test_create_and_get_note(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        create = NoteCreateSchema(title="My Note", body="Hello world", folder_id=root_folder.id)
        note = NoteService.create_note(test_db, user_id=test_user.id, create_data=create)

        assert note.id is not None
        assert note.title == "My Note"
        assert note.body == "Hello world"
        assert note.user_id == test_user.id

        fetched = NoteService.get_note(test_db, note_id=note.id, user_id=test_user.id)
        assert fetched is not None
        assert fetched.id == note.id

    def test_update_note(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title='', body="old", folder_id=root_folder.id)
        )
        updated = NoteService.update_note(
            test_db,
            note_id=note.id,
            user_id=test_user.id,
            update_data=NoteUpdateSchema(title="New Title", body="new")
        )
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.body == "new"

    def test_mark_note_as_deleted(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(body="to delete",folder_id=root_folder.id)
        )
        ok = NoteService.delete_note(test_db, note_id=note.id, user_id=test_user.id)
        assert ok is True

        # Should not appear in base query anymore
        found = NoteService.get_note(test_db, note_id=note.id, user_id=test_user.id)
        assert found is None

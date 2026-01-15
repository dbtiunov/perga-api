from sqlalchemy.orm import Session

from app.services.note_service import NoteService
from app.schemas.note import NoteCreate, NoteUpdate
from app.models.note import Note


class TestNoteService:
    def test_create_and_get_note(self, test_db: Session, test_user):
        create = NoteCreate(title="My Note", body="Hello world")
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
        NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreate(body="A"))
        # Create a note for another user
        other = Note(title="Other", body="B", user_id=test_user.id + 1)
        test_db.add(other)
        test_db.commit()

        notes = NoteService.list_notes(test_db, user_id=test_user.id)
        assert len(notes) == 1
        assert notes[0].user_id == test_user.id

    def test_update_note(self, test_db: Session, test_user):
        note = NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreate(title=None, body="old"))
        updated = NoteService.update_note(
            test_db,
            note_id=note.id,
            user_id=test_user.id,
            note_in=NoteUpdate(title="New Title", body="new")
        )
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.body == "new"

    def test_delete_note_soft(self, test_db: Session, test_user):
        note = NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreate(body="to delete"))
        ok = NoteService.delete_note(test_db, note_id=note.id, user_id=test_user.id)
        assert ok is True

        # Should not appear in base query anymore
        found = NoteService.get_note(test_db, note_id=note.id, user_id=test_user.id)
        assert found is None

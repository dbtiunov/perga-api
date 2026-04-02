from sqlalchemy.orm import Session
from app.schemas.notes import NoteCreateSchema, NoteUpdateSchema
from app.services.notes_folders_service import NotesFolderService
from app.services.notes_service import NoteService
from app.services.notes_import_service import NotesImportService

class TestNoteSanitization:
    def test_create_note_with_malicious_html(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        malicious_body = "<p>Safe content</p><script>alert('xss')</script><img src='x' onerror='alert(1)'>"
        create = NoteCreateSchema(title="Malicious Note", body=malicious_body, folder_id=root_folder.id)
        
        note = NoteService.create_note(test_db, user_id=test_user.id, create_data=create)
        
        # Now it SHOULD be sanitized.
        assert "<script>" not in note.body
        assert "onerror" not in note.body
        assert "<p>Safe content</p>" in note.body

    def test_update_note_with_malicious_html(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Initial", body="Initial body", folder_id=root_folder.id)
        )
        
        malicious_body = "<div onclick='alert(1)'>Click me</div>"
        updated = NoteService.update_note(
            test_db,
            note_id=note.id,
            user_id=test_user.id,
            update_data=NoteUpdateSchema(body=malicious_body)
        )
        
        assert "onclick" not in updated.body
        assert "<div>Click me</div>" in updated.body

    def test_import_note_with_malicious_html(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        malicious_html = "<html><head><title>Bad Note</title></head><body><script>alert(1)</script><p>Imported content</p></body></html>"
        
        note = NotesImportService.import_file(
            test_db, 
            user_id=test_user.id, 
            filename="bad.html", 
            content=malicious_html.encode('utf-8'), 
            folder_id=root_folder.id
        )
        
        assert note is not None
        assert "<script>" not in note.body
        assert "<p>Imported content</p>" in note.body

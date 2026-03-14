import zipfile
from sqlalchemy.orm import Session

from app.models.notes import Note
from app.services.notes_export_service import NotesExportService
from app.services.notes_service import NoteService
from app.services.notes_folders_service import NotesFolderService
from app.schemas.notes import NoteCreateSchema
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.const.notes import ExportType

class TestNotesExportService:
    def test_get_note_content_html(self, test_db: Session, test_user):
        note = Note(title="Test", body="<h1>Hello</h1>", user_id=test_user.id)
        content = NotesExportService._get_note_content(note, ExportType.HTML)
        assert content == "<h1>Hello</h1>"

    def test_get_note_content_markdown(self, test_db: Session, test_user):
        note = Note(title="Test", body="<h1>Hello</h1>", user_id=test_user.id)
        content = NotesExportService._get_note_content(note, ExportType.MARKDOWN)
        assert "Hello" in content
        # markdownify might use different styles, but let's check for some common markers
        assert "=====" in content or "# Hello" in content

    def test_generate_export_filename(self, test_db: Session, test_user):
        note = Note(id=1, title="My Note!", body="", user_id=test_user.id)
        filename = NotesExportService._generate_export_filename(note, ExportType.HTML)
        assert filename == "My Note.html"

        note_no_title = Note(id=2, title="!!!", body="", user_id=test_user.id)
        filename = NotesExportService._generate_export_filename(note_no_title, ExportType.MARKDOWN)
        assert filename == "note_2.md"

    def test_export_single_note(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Test", body="Body", folder_id=root_folder.id)
        )
        
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.HTML
        )
        assert content == "Body"
        assert filename == "Test.html"

    def test_export_folder(self, test_db: Session, test_user):
        folder = NotesFolderService.create_folder(
            test_db, user_id=test_user.id, create_data=NotesFolderCreateSchema(name="Folder")
        )
        NoteService.create_note(
            test_db, user_id=test_user.id, create_data=NoteCreateSchema(title="Note 1", body="B1", folder_id=folder.id)
        )
        
        zip_buffer, filename = NotesExportService.export_folder(
            test_db, user_id=test_user.id, folder_id=folder.id, export_type=ExportType.HTML
        )
        assert zip_buffer is not None
        assert filename == "notes_folder_Folder.zip"
        
        with zipfile.ZipFile(zip_buffer) as zf:
            assert "Note 1.html" in zf.namelist()

    def test_export_all_notes(self, test_db: Session, test_user):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Note 1", body="B1", folder_id=root_folder.id)
        )
        
        zip_buffer, filename = NotesExportService.export_all_notes(
            test_db, user_id=test_user.id, export_type=ExportType.HTML
        )
        assert zip_buffer is not None
        assert filename == "all_notes.zip"
        
        with zipfile.ZipFile(zip_buffer) as zf:
            assert "Note 1.html" in zf.namelist()

    def test_create_zip_archive_duplicates(self, test_db: Session, test_user):
        note1 = Note(id=1, title="Same", body="B1", user_id=test_user.id)
        note2 = Note(id=2, title="Same", body="B2", user_id=test_user.id)
        
        zip_buffer = NotesExportService._create_zip_archive([note1, note2], ExportType.HTML)
        
        with zipfile.ZipFile(zip_buffer) as zf:
            names = zf.namelist()
            assert "Same.html" in names
            assert "Same_1.html" in names

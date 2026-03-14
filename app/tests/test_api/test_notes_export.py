import io
import zipfile
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.notes_service import NoteService
from app.services.notes_folders_service import NotesFolderService
from app.schemas.notes import NoteCreateSchema
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.const.notes import ExportType, ExportTarget

class TestNotesExportAPI:
    def test_export_single_note_html(self, client: TestClient, test_db: Session, test_user, auth_headers):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(
                title="Test Note",
                body="<h1>Hello</h1><p>World</p>",
                folder_id=root_folder.id
            )
        )
        
        response = client.post(
            "/api/v1/notes/export/",
            json={
                "export_type": ExportType.HTML,
                "export_target": ExportTarget.SINGLE_NOTE,
                "export_target_id": note.id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "attachment; filename=Test Note.html" in response.headers["content-disposition"]
        assert response.text == "<h1>Hello</h1><p>World</p>"

    def test_export_single_note_markdown(self, client: TestClient, test_db: Session, test_user, auth_headers):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(
                title="Test Note",
                body="<h1>Hello</h1><p>World</p>",
                folder_id=root_folder.id
            )
        )
        
        response = client.post(
            "/api/v1/notes/export/",
            json={
                "export_type": ExportType.MARKDOWN,
                "export_target": ExportTarget.SINGLE_NOTE,
                "export_target_id": note.id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "text/markdown" in response.headers["content-type"]
        assert "attachment; filename=Test Note.md" in response.headers["content-disposition"]
        # markdownify of <h1>Hello</h1><p>World</p> should be something like "Hello\n=====\n\nWorld\n\n"
        assert "Hello" in response.text
        assert "World" in response.text

    def test_export_folder_zip(self, client: TestClient, test_db: Session, test_user, auth_headers):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        folder = NotesFolderService.create_folder(
            test_db,
            user_id=test_user.id,
            create_data=NotesFolderCreateSchema(name="My Folder", parent_id=root_folder.id)
        )
        
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Note 1", body="Body 1", folder_id=folder.id)
        )
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Note 2", body="Body 2", folder_id=folder.id)
        )
        
        response = client.post(
            "/api/v1/notes/export/",
            json={
                "export_type": ExportType.MARKDOWN,
                "export_target": ExportTarget.FOLDER_NOTES,
                "export_target_id": folder.id
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/x-zip-compressed"
        assert f"attachment; filename=notes_folder_{folder.name}.zip" in response.headers["content-disposition"]
        
        # Verify ZIP content
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content) as zf:
            filenames = zf.namelist()
            assert "Note 1.md" in filenames
            assert "Note 2.md" in filenames
            assert zf.read("Note 1.md").decode().strip() == "Body 1"

    def test_export_all_notes_zip(self, client: TestClient, test_db: Session, test_user, auth_headers):
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Root Note", body="Root Body", folder_id=root_folder.id)
        )
        
        folder = NotesFolderService.create_folder(
            test_db,
            user_id=test_user.id,
            create_data=NotesFolderCreateSchema(name="Subfolder", parent_id=root_folder.id)
        )
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title="Sub Note", body="Sub Body", folder_id=folder.id)
        )
        
        response = client.post(
            "/api/v1/notes/export/",
            json={
                "export_type": ExportType.HTML,
                "export_target": ExportTarget.ALL_NOTES
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "attachment; filename=all_notes.zip" in response.headers["content-disposition"]
        
        zip_content = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_content) as zf:
            filenames = zf.namelist()
            assert "Root Note.html" in filenames
            assert "Sub Note.html" in filenames

    def test_export_not_found(self, client: TestClient, test_user, auth_headers):
        response = client.post(
            "/api/v1/notes/export/",
            json={
                "export_type": ExportType.MARKDOWN,
                "export_target": ExportTarget.SINGLE_NOTE,
                "export_target_id": 9999
            },
            headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Note not found"

    def test_export_bad_request(self, client: TestClient, test_user, auth_headers):
        # Missing export_target
        response = client.post(
            "/api/v1/notes/export/",
            json={"export_type": ExportType.MARKDOWN},
            headers=auth_headers
        )
        assert response.status_code == 422

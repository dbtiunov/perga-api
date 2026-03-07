from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.schemas.notes import NoteCreateSchema
from app.services.notes_folders_service import NotesFolderService
from app.services.notes_service import NoteService

class TestNotesFolderAPI:
    def test_get_folders_excludes_note_body(self, client: TestClient, test_db: Session, test_user, auth_headers):
        # 1. Create a folder and a note with a body
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note_title = "Secret Note"
        note_body = "This is a secret body that should not be in the folders list"
        
        NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(
                title=note_title,
                body=note_body,
                folder_id=root_folder.id
            )
        )
        
        # 2. Call the get_folders API
        response = client.get("/api/v1/notes/folders/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # 3. Verify the note is present but body is missing
        root_folder_data = data["root_folder"]
        notes = root_folder_data["notes"]
        
        assert len(notes) > 0
        note_data = notes[0]
        assert note_data["title"] == note_title
        assert "body" not in note_data

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.notes_service import NoteService
from app.services.notes_folders_service import NotesFolderService
from app.schemas.notes import NoteCreateSchema
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.services.auth_service import AuthService

def get_auth_headers(user_id: int):
    tokens = AuthService.create_user_tokens(user_id)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

def test_get_folders(client: TestClient, test_db: Session, test_user):
    # 1. Setup folders and notes
    # Root folder 1 (will be child of Root automatically)
    f1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, request_data=NotesFolderCreateSchema(name="Root 1"))
    # Subfolder of Root 1
    sf1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, request_data=NotesFolderCreateSchema(name="Sub 1", parent_id=f1.id))
    # Root folder 2
    f2 = NotesFolderService.create_folder(test_db, user_id=test_user.id, request_data=NotesFolderCreateSchema(name="Root 2"))
    
    # Note in sf1
    NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreateSchema(title="Note 1", body="Content 1", folder_id=sf1.id))
    
    headers = get_auth_headers(test_user.id)
    
    # 2. Test tree without notes
    response = client.get("/api/v1/notes/folders/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    assert "root_folder" in data
    assert "trash_folder" in data
    
    root_folder = data["root_folder"]
    assert root_folder["name"] == "Root"
    assert len(root_folder["subfolders"]) == 2
    
    # Find Root 1
    root1 = next(f for f in root_folder["subfolders"] if f["name"] == "Root 1")
    assert len(root1["subfolders"]) == 1
    assert root1["subfolders"][0]["name"] == "Sub 1"
    
    # 3. Test tree with notes
    response = client.get("/api/v1/notes/folders/?include_notes=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    root_folder = data["root_folder"]
    root1 = next(f for f in root_folder["subfolders"] if f["name"] == "Root 1")
    sub1 = root1["subfolders"][0]
    assert len(sub1["notes"]) == 1
    assert sub1["notes"][0]["title"] == "Note 1"

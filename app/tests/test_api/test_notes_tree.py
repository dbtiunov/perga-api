import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.notes_service import NoteService, NotesFolderService
from app.schemas.notes import NoteCreateSchema, NotesFolderCreateSchema
from app.services.auth_service import AuthService

def get_auth_headers(user_id: int):
    tokens = AuthService.create_user_tokens(user_id)
    return {"Authorization": f"Bearer {tokens['access_token']}"}

def test_get_folders_tree(client: TestClient, test_db: Session, test_user):
    # 1. Setup folders and notes
    # Root folder 1
    f1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="Root 1"))
    # Subfolder of Root 1
    sf1 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="Sub 1", parent_id=f1.id))
    # Root folder 2
    f2 = NotesFolderService.create_folder(test_db, user_id=test_user.id, folder_in=NotesFolderCreateSchema(name="Root 2"))
    
    # Note in sf1
    NoteService.create_note(test_db, user_id=test_user.id, note_in=NoteCreateSchema(title="Note 1", body="Content 1", folder_id=sf1.id))
    
    headers = get_auth_headers(test_user.id)
    
    # 2. Test tree without notes
    response = client.get("/api/v1/notes/folders/tree/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # 2 regular roots + 1 trash root
    assert len(data) == 3
    # Find Root 1
    root1 = next(f for f in data if f["name"] == "Root 1")
    assert len(root1["subfolders"]) == 1
    assert root1["subfolders"][0]["name"] == "Sub 1"
    assert "notes" not in root1 or not root1["notes"] # Should not be there if not requested or empty
    
    # 3. Test tree with notes
    response = client.get("/api/v1/notes/folders/tree/?include_notes=true", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    root1 = next(f for f in data if f["name"] == "Root 1")
    sub1 = root1["subfolders"][0]
    assert len(sub1["notes"]) == 1
    assert sub1["notes"][0]["title"] == "Note 1"

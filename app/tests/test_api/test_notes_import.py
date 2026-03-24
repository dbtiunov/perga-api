import io
import zipfile
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.notes_folders_service import NotesFolderService
from app.schemas.notes_folders import NotesFolderCreateSchema

def test_import_files(client: TestClient, auth_headers: dict, test_db: Session, test_user):
    files = [
        ("files", ("test1.txt", b"Hello from TXT")),
        ("files", ("test2.md", b"# Markdown Title\nBody")),
    ]
    response = client.post("/api/v1/notes/import/", files=files, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 2
    
    # Check that a new import folder was created
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder = NotesFolderService.get_base_query(test_db).filter_by(
        name=f"import_{current_date}", user_id=test_user.id
    ).first()
    assert folder is not None
    
    # Check that notes were created in the database
    from app.models.notes import Note
    notes = test_db.query(Note).filter_by(folder_id=folder.id).all()
    assert len(notes) == 2
    
    titles = [note.title for note in notes]
    assert "test1" in titles
    assert "Markdown Title" in titles

def test_import_multiple_times(client: TestClient, auth_headers: dict, test_db: Session, test_user):
    # First import
    client.post("/api/v1/notes/import/", files=[("files", ("t1.txt", b"c1"))], headers=auth_headers)
    
    # Second import
    client.post("/api/v1/notes/import/", files=[("files", ("t2.txt", b"c2"))], headers=auth_headers)
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    folder1 = NotesFolderService.get_base_query(test_db).filter_by(
        name=f"import_{current_date}", user_id=test_user.id
    ).first()
    folder2 = NotesFolderService.get_base_query(test_db).filter_by(
        name=f"import_{current_date}_1", user_id=test_user.id
    ).first()
    
    assert folder1 is not None
    assert folder2 is not None
    assert folder1.id != folder2.id

def test_import_zip(client: TestClient, auth_headers: dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr("zipped.txt", "In ZIP")
    
    files = [
        ("files", ("archive.zip", zip_buffer.getvalue())),
    ]
    response = client.post("/api/v1/notes/import/", files=files, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 1


def test_import_invalid_file(client: TestClient, auth_headers: dict):
    files = [
        ("files", ("image.png", b"not a text file")),
    ]
    response = client.post("/api/v1/notes/import/", files=files, headers=auth_headers)
    # Our implementation currently skips invalid files, but if NO notes were imported it returns 400
    assert response.status_code == 400
    assert "No valid notes found" in response.json()["detail"]

def test_import_with_folder_id(client: TestClient, auth_headers: dict, test_db: Session, test_user):
    # Create a target folder
    folder = NotesFolderService.create_folder(
        test_db,
        user_id=test_user.id,
        create_data=NotesFolderCreateSchema(name="Target Folder")
    )
    
    files = [
        ("files", ("test.txt", b"Hello")),
    ]
    # Import with folder_id
    response = client.post(
        f"/api/v1/notes/import/?folder_id={folder.id}",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["imported_count"] == 1
    
    # Check that the note was created in the correct folder
    from app.models.notes import Note
    note = test_db.query(Note).filter_by(folder_id=folder.id).first()
    assert note is not None
    assert note.title == "test"

def test_import_with_invalid_folder_id(client: TestClient, auth_headers: dict):
    files = [
        ("files", ("test.txt", b"Hello")),
    ]
    # Import with non-existent folder_id
    response = client.post(
        "/api/v1/notes/import/?folder_id=9999",
        files=files,
        headers=auth_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Folder not found"

def test_import_large_file_limit(client: TestClient, auth_headers: dict):
    # This test currently fails because there's no limit
    large_content = b"a" * (11 * 1024 * 1024) # 11 MB
    files = [
        ("files", ("large.txt", large_content)),
    ]
    response = client.post("/api/v1/notes/import/", files=files, headers=auth_headers)
    assert response.status_code == 413
    assert "is too large" in response.json()["detail"]


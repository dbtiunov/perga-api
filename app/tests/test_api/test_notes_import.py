import io
import zipfile
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notes import Note
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.services.notes_folders_service import NotesFolderService


class TestNotesImport:
    def test_import_files(self, client: TestClient, auth_headers: dict, test_db: Session, test_user):
        files = [
            ('files', ('test1.txt', b'Hello from TXT')),
            ('files', ('test2.md', b'# Markdown Title\nBody')),
        ]
        response = client.post(f'{settings.API_V1_STR}/notes/import/', files=files, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data['imported_count'] == 2
        
        # Check that the notes were created in the root folder
        root_folder = NotesFolderService.get_root_folder(test_db, test_user.id)
        
        # Check that notes were created in the database
        notes = test_db.query(Note).filter_by(folder_id=root_folder.id).all()
        assert len(notes) == 2
        
        titles = [note.title for note in notes]
        assert 'test1' in titles
        assert 'Markdown Title' in titles


    def test_import_multiple_times(self, client: TestClient, auth_headers: dict, test_db: Session, test_user):
        # First import
        client.post(
            f'{settings.API_V1_STR}/notes/import/',
            files=[('files', ('t1.txt', b'c1'))],
            headers=auth_headers
        )
        
        # Second import
        client.post(
            f'{settings.API_V1_STR}/notes/import/',
            files=[('files', ('t2.txt', b'c2'))],
            headers=auth_headers
        )
        
        # Check that both notes are in the root folder
        root_folder = NotesFolderService.get_root_folder(test_db, test_user.id)
        notes = test_db.query(Note).filter_by(folder_id=root_folder.id).all()
        assert len(notes) == 2

    def test_import_zip(self, client: TestClient, auth_headers: dict):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            zip_file.writestr('zipped.txt', 'In ZIP')
        
        files = [
            ('files', ('archive.zip', zip_buffer.getvalue())),
        ]
        response = client.post(
            f'{settings.API_V1_STR}/notes/import/',
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['imported_count'] == 1


    def test_import_invalid_file(self, client: TestClient, auth_headers: dict):
        files = [
            ('files', ('image.png', b'not a text file')),
        ]
        response = client.post(
            f'{settings.API_V1_STR}/notes/import/',
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert 'No valid notes found' in response.json()['detail']


    def test_import_with_folder_id(self, client: TestClient, auth_headers: dict, test_db: Session, test_user):
        # Create a target folder
        folder = NotesFolderService.create_folder(
            test_db,
            user_id=test_user.id,
            create_data=NotesFolderCreateSchema(name='Target Folder')
        )
        
        files = [
            ('files', ('test.txt', b'Hello')),
        ]
        # Import with folder_id
        response = client.post(
            f'{settings.API_V1_STR}/notes/import/?folder_id={folder.id}',
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data['imported_count'] == 1
        
        # Check that the note was created in the correct folder
        note = test_db.query(Note).filter_by(folder_id=folder.id).first()
        assert note is not None
        assert note.title == 'test'


    def test_import_with_invalid_folder_id(self, client: TestClient, auth_headers: dict):
        files = [
            ('files', ('test.txt', b'Hello')),
        ]
        # Import with non-existent folder_id
        response = client.post(
            f'{settings.API_V1_STR}/notes/import/?folder_id=123',
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 404
        assert response.json()['detail'] == 'Folder not found'

    def test_import_large_file_limit(self, client: TestClient, auth_headers: dict):
        large_content = b'a' * (11 * 1024 * 1024) # 11 MB
        files = [
            ('files', ('large.txt', large_content)),
        ]
        response = client.post(
            f'{settings.API_V1_STR}/notes/import/',
            files=files,
            headers=auth_headers
        )
        assert response.status_code == 413
        assert 'is too large' in response.json()['detail']

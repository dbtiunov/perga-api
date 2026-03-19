import io
import os
import zipfile
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.notes import Note
from app.schemas.notes import NoteCreateSchema
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.services.notes_service import NoteService
from app.services.notes_folders_service import NotesFolderService


class NotesImportService:
    @classmethod
    def _parse_html(cls, content: str) -> tuple[str, str]:
        soup = BeautifulSoup(content, 'html.parser')
        
        # try to find a title
        title = ''
        if soup.title:
            title = soup.title.string
        elif soup.h1:
            title = soup.h1.get_text()
            
        if soup.body:
            body = ''.join(str(tag) for tag in soup.body.contents)
        else:
            body = content
            
        return title or 'Untitled Note', body

    @classmethod
    def _parse_markdown(cls, content: str) -> tuple[str, str]:
        lines = content.splitlines()
        title = 'Untitled Note'
        body_start_index = 0
        
        for index, line in enumerate(lines):
            if line.startswith('# '):
                title = line[2:].strip()
                body_start_index = index + 1
                break
        
        body = '\n'.join(lines[body_start_index:]).strip()
        return title, body

    @classmethod
    def _parse_txt(cls, content: str, filename: str) -> tuple[str, str]:
        title = os.path.splitext(filename)[0]
        return title, content

    @classmethod
    def import_file(
        cls, db: Session, user_id: int, filename: str, content: bytes, folder_id: int
    ) -> Note | None:
        """ Import a single file as a note. """
        extension = os.path.splitext(filename)[1].lower()
        
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            # skip non utf-8 files
            return None

        if extension == '.md':
            title, body = cls._parse_markdown(text_content)
        elif extension in ('.html', '.htm'):
            title, body = cls._parse_html(text_content)
        elif extension == '.txt':
            title, body = cls._parse_txt(text_content, filename)
        else:
            return None

        return NoteService.create_note(
            db,
            user_id,
            NoteCreateSchema(folder_id=folder_id, title=title, body=body)
        )

    @classmethod
    def import_zip(
        cls, db: Session, user_id: int, zip_content: bytes, folder_id: int
    ) -> list[Note]:
        """ Import a ZIP archive, preserving folder structure. """
        imported_notes = []

        zip_buffer = io.BytesIO(zip_content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # keep track of created folders to reuse them: { <path>: <folder_id> }
            created_folders_map = {'': folder_id}
            
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    path_parts = [part for part in file_info.filename.strip('/').split('/') if part]
                    current_path = ''
                    current_parent_id = folder_id
                    
                    for part in path_parts:
                        full_part_path = f'{current_path}/{part}'.strip('/')
                        if full_part_path not in created_folders_map:
                            new_folder = NotesFolderService.create_folder(
                                db,
                                user_id,
                                NotesFolderCreateSchema(parent_id=current_parent_id, name=part)
                            )
                            created_folders_map[full_part_path] = new_folder.id
                        
                        current_path = full_part_path
                        current_parent_id = created_folders_map[full_part_path]
                    continue
                
                # Handle file entry
                filename = file_info.filename
                path_parts = filename.split('/')
                
                if len(path_parts) > 1:
                    # File is in a subfolder
                    base_filename = path_parts[-1]
                    
                    # Ensure all parent folders exist
                    current_path = ''
                    current_parent_id = folder_id
                    for part in path_parts[:-1]:
                        full_part_path = f'{current_path}/{part}'.strip('/')
                        if full_part_path not in created_folders_map:
                            new_folder = NotesFolderService.create_folder(
                                db,
                                user_id,
                                NotesFolderCreateSchema(parent_id=current_parent_id, name=part)
                            )
                            created_folders_map[full_part_path] = new_folder.id
                        current_path = full_part_path
                        current_parent_id = created_folders_map[full_part_path]
                    
                    target_folder_id = current_parent_id
                else:
                    base_filename = filename
                    target_folder_id = folder_id
                
                # import the file
                with zip_ref.open(file_info) as f:
                    content = f.read()
                    note = cls.import_file(db, user_id, base_filename, content, target_folder_id)
                    if note:
                        imported_notes.append(note)
                        
        return imported_notes

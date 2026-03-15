import io
import zipfile
from markdownify import markdownify
from weasyprint import HTML
from sqlalchemy.orm import Session

from app.const.notes import ExportType, EXPORT_TYPE_EXTENSION_MAP
from app.models.notes import Note, NotesFolder
from app.services.notes_service import NoteService
from app.services.notes_folders_service import NotesFolderService


class NotesExportService:
    @classmethod
    def _generate_pdf_content(cls, note: Note) -> bytes:
        """ Generate PDF content from note body HTML. """
        html_content = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 40px; }}
                    h1 {{ font-size: 24px; margin-bottom: 16px; }}
                </style>
            </head>
            <body>
                <h1>{note.title}</h1>
                {note.body}
            </body>
            </html>
        """
        return HTML(string=html_content).write_pdf()

    @classmethod
    def _get_note_content(cls, note: Note, export_type: ExportType) -> str | bytes:
        """ Notes body stored as HTML. Converts it to a specified format if needed and adds a title. """
        note_content: str | bytes
        if export_type == ExportType.MARKDOWN:
            title = f"# {note.title}\n\n"
            note_content = title + markdownify(note.body)
        elif export_type == ExportType.PDF:
            note_content = cls._generate_pdf_content(note)
        else:
            title = f"<h1>{note.title}</h1>"
            note_content = title + note.body
        return note_content

    @classmethod
    def _generate_export_filename(cls, note: Note, export_type: ExportType) -> str:
        extension = EXPORT_TYPE_EXTENSION_MAP[export_type]

        # sanitiza filename
        safe_title = ''.join(
            [char for char in note.title if char.isalnum() or char in (' ', '.', '_')]
        ).rstrip()
        if not safe_title:
            safe_title = f'note_{note.id}'

        return f'{safe_title}.{extension}'

    @classmethod
    def _create_zip_archive(cls, notes: list[Note], export_type: ExportType) -> io.BytesIO:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
            used_filenames = set()
            for note in notes:
                content = cls._get_note_content(note, export_type)
                base_filename = cls._generate_export_filename(note, export_type)

                # Handle duplicate filenames in ZIP
                filename = base_filename
                counter = 1
                while filename in used_filenames:
                    name_parts = base_filename.rsplit('.', 1)
                    filename = f'{name_parts[0]}_{counter}.{name_parts[1]}'
                    counter += 1

                used_filenames.add(filename)
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)
        return zip_buffer

    @classmethod
    def _get_all_notes_in_folder(cls, folder: NotesFolder) -> list[Note]:
        notes = [note for note in folder.notes if not note.is_deleted]
        for subfolder in folder.subfolders:
            if not subfolder.is_deleted:
                notes.extend(cls._get_all_notes_in_folder(subfolder))
        return notes

    @classmethod
    def export_single_note(
        cls, db: Session, user_id: int, note_id: int, export_type: ExportType
    ) -> tuple[str | bytes, str] | tuple[None, None]:
        note = NoteService.get_note(db, note_id=note_id, user_id=user_id)
        if not note:
            return None, None

        content = cls._get_note_content(note, export_type)
        filename = cls._generate_export_filename(note, export_type)
        return content, filename

    @classmethod
    def export_folder(
        cls, db: Session, user_id: int, folder_id: int, export_type: ExportType
    ) -> tuple[io.BytesIO, str] | tuple[None, None]:
        folder = NotesFolderService.get_folder(db, folder_id=folder_id, user_id=user_id)
        if not folder:
            return None, None
        
        notes = cls._get_all_notes_in_folder(folder)
        return cls._create_zip_archive(notes, export_type), f'notes_folder_{folder.name}.zip'

    @classmethod
    def export_all_notes(
        cls, db: Session, user_id: int, export_type: ExportType
    ) -> tuple[io.BytesIO, str] | tuple[None, None]:
        notes = NoteService.get_base_query(db).filter(Note.user_id == user_id).all()
        if not notes:
            return None, None

        return cls._create_zip_archive(notes, export_type), 'all_notes.zip'

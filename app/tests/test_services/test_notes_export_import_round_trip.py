from sqlalchemy.orm import Session

from app.const.notes import ExportType
from app.schemas.notes import NoteCreateSchema
from app.schemas.notes_folders import NotesFolderCreateSchema
from app.services.notes_export_service import NotesExportService
from app.services.notes_import_service import NotesImportService
from app.services.notes_folders_service import NotesFolderService
from app.services.notes_service import NoteService


class TestNotesExportImportRoundTrip:
    def test_html_round_trip(self, test_db: Session, test_user):
        # 1. Create a note
        title = "Original Title"
        body = "<p>Original Body Content</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to HTML
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.HTML
        )
        
        # 3. Import the content back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db,
            test_user.id,
            filename,
            content.encode('utf-8') if isinstance(content, str) else content,
            import_folder.id
        )

        # 4. Verify round-trip results
        assert imported_note is not None
        assert imported_note.title == title
        # Note: ExportService adds <h1>Title</h1> to the body for HTML.
        # ImportService._parse_html extracts <h1> and REMOVES it from the body IF there is no <title> tag.
        # NotesExportService.export_single_note doesn't add <title> or <body> tags, it just concatenates.
        assert imported_note.body.strip() == body.strip()

    def test_markdown_round_trip(self, test_db: Session, test_user):
        # 1. Create a note
        title = "Markdown Title"
        body = "<p>Body with <strong>bold</strong> text.</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db, user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to Markdown
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.MARKDOWN
        )
        
        # 3. Import the content back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db,
            test_user.id,
            filename,
            content.encode('utf-8') if isinstance(content, str) else content,
            import_folder.id
        )

        # 4. Verify round-trip results
        assert imported_note is not None
        assert imported_note.title == title
        # Markdown roundtrip is lossy as it converts HTML -> MD -> HTML
        # We expect at least the text content to be preserved.
        assert "Body with" in imported_note.body
        assert "bold" in imported_note.body

    def test_markdown_newlines_round_trip(self, test_db: Session, test_user):
        # 1. Create a note with multiple paragraphs (double newlines in HTML)
        title = "Markdown Newlines"
        # In HTML, double newlines are represented by separate <p> tags or <p></p><p></p>
        body = "<p>Paragraph 1</p><p>Paragraph 2</p><p>Line 1</p><p>Line 2</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db, user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to Markdown
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.MARKDOWN
        )
        
        # 3. Import the content back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db, test_user.id, filename, content.encode('utf-8'), import_folder.id
        )

        # 4. Verify round-trip results
        assert imported_note is not None
        assert imported_note.title == title
        
        # We expect Paragraph 1 and Paragraph 2 to be in separate <p> tags
        # and Line 1 / Line 2 to be in separate <p> tags
        assert "<p>Paragraph 1</p>" in imported_note.body
        assert "<p>Paragraph 2</p>" in imported_note.body
        assert "<p>Line 1</p>" in imported_note.body
        assert "<p>Line 2</p>" in imported_note.body

    def test_markdown_many_newlines_round_trip(self, test_db: Session, test_user):
        # 1. Create a note with many newlines
        title = "Many Newlines"
        # 3 empty paragraphs between lines
        body = "<p>Line 1</p><p></p><p></p><p></p><p>Line 2</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db, user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to Markdown
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.MARKDOWN
        )
        
        # 3. Import the content back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db, test_user.id, filename, content.encode('utf-8'), import_folder.id
        )

        # 4. Verify round-trip results
        # Markdownify often collapses multiple empty <p> tags into single newlines.
        # We check if we still have two lines
        assert "Line 1" in imported_note.body
        assert "Line 2" in imported_note.body
        # Check if they are separated.
        # markdown.markdown normally creates <p> for blocks separated by double newline.

    def test_markdown_single_newlines_round_trip(self, test_db: Session, test_user):
        # 1. Create a note with single newlines in body
        title = "Single Newlines"
        # markdownify should preserve single newlines (using paragraphs)
        body = "<p>Line 1</p><p>Line 2</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db, user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to Markdown
        content, _ = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.MARKDOWN
        )
        
        # 3. Import back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db, test_user.id, "test.md", content.encode('utf-8'), import_folder.id
        )

        # 4. Verify
        # nl2br should handle single newline in MD (converted to <p> tags if separated)
        assert "Line 1" in imported_note.body
        assert "Line 2" in imported_note.body

    def test_markdown_triple_newlines_round_trip(self, test_db: Session, test_user):
        # 1. Create a note with triple newlines in MD
        # In MD, triple newlines (2 empty lines) are usually just a paragraph break
        title = "Triple Newlines"
        # markdownify of <p>A</p><p>B</p> is A\n\nB
        # If we want 3 newlines, we'd need <p>A</p><p></p><p>B</p> maybe?
        body = "<p>Line 1</p><p><p></p></p><p>Line 2</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db, user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export
        content, _ = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.MARKDOWN
        )
        
        # 3. Import
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db, test_user.id, "test.md", content.encode('utf-8'), import_folder.id
        )

        # 4. Verify
        # We expect at least two paragraphs
        assert "Line 1" in imported_note.body
        assert "Line 2" in imported_note.body

    def test_html_round_trip_with_h1_in_body(self, test_db: Session, test_user):
        # 1. Create a note where body STARTS with H1
        title = "Original Title"
        body = "<h1>My H1</h1><p>Original Body Content</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            user_id=test_user.id,
            create_data=NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export the note to HTML
        # Content will be <h1>Original Title</h1><h1>My H1</h1><p>Original Body Content</p>
        content, filename = NotesExportService.export_single_note(
            test_db, user_id=test_user.id, note_id=note.id, export_type=ExportType.HTML
        )
        
        # 3. Import the content back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db,
            test_user.id,
            filename,
            content.encode('utf-8') if isinstance(content, str) else content,
            import_folder.id
        )

        # 4. Verify round-trip results
        assert imported_note is not None
        assert imported_note.title == title
        # Suspected issue: ImportService finds FIRST <h1> (which is Original Title),
        # uses it as title, and DELETES it.
        # The remaining body should be "<h1>My H1</h1><p>Original Body Content</p>"
        assert imported_note.body.strip() == body.strip()

    def test_zip_folder_recursive_round_trip(self, test_db: Session, test_user):
        # 1. Create folder structure with notes
        parent = NotesFolderService.create_folder(
            test_db, test_user.id, NotesFolderCreateSchema(name="ParentFolder")
        )
        child = NotesFolderService.create_folder(
            test_db, test_user.id, NotesFolderCreateSchema(name="ChildFolder", parent_id=parent.id)
        )
        
        NoteService.create_note(
            test_db,
            test_user.id,
            NoteCreateSchema(title="Note 1", body="<p>Body 1</p>", folder_id=parent.id)
        )
        NoteService.create_note(test_db, test_user.id, NoteCreateSchema(
            title="Note 2",
            body="<p>Body 2</p>",
            folder_id=child.id)
        )

        # 2. Export the parent folder to HTML ZIP
        zip_buffer, filename = NotesExportService.export_folder(
            test_db, user_id=test_user.id, folder_id=parent.id, export_type=ExportType.HTML
        )
        
        # 3. Import the ZIP back
        import_root = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_notes = NotesImportService.import_zip(
            test_db, test_user.id, zip_buffer.getvalue(), import_root.id
        )

        # 4. Verify structure
        assert len(imported_notes) == 2
        
        # Find imported notes
        _note1 = next(n for n in imported_notes if n.title == "Note 1")
        note2 = next(n for n in imported_notes if n.title == "Note 2")
        
        # Verify if Note 2 is in a subfolder named "ChildFolder"
        # Current implementation of ExportService.export_folder is FLAT.
        # So we expect this to FAIL if we want structure preservation.
        folder2 = NotesFolderService.get_folder(test_db, note2.folder_id, test_user.id)
        assert folder2.name == "ChildFolder"
        assert folder2.parent_id is not None
        parent_of_2 = NotesFolderService.get_folder(test_db, folder2.parent_id, test_user.id)
        assert parent_of_2.name == "ParentFolder" or parent_of_2.id == import_root.id

    def test_duplicate_titles_round_trip(self, test_db: Session, test_user):
        # 1. Create two notes with same title in same folder
        title = "Duplicate"
        folder = NotesFolderService.create_folder(test_db, test_user.id, NotesFolderCreateSchema(name="DupFolder"))
        NoteService.create_note(test_db, test_user.id, NoteCreateSchema(
            title=title,
            body="Body 1",
            folder_id=folder.id)
        )
        NoteService.create_note(test_db, test_user.id, NoteCreateSchema(
            title=title,
            body="Body 2",
            folder_id=folder.id)
        )

        # 2. Export folder to HTML ZIP
        zip_buffer, _ = NotesExportService.export_folder(test_db, test_user.id, folder.id, ExportType.HTML)

        # 3. Import back
        import_root = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_notes = NotesImportService.import_zip(test_db, test_user.id, zip_buffer.getvalue(), import_root.id)

        # 4. Verify
        assert len(imported_notes) == 2
        # Both will be "Duplicate" because ImportService extracts title from <h1> in the body,
        # which is the original title. ZIP filename is only used as fallback.
        titles = {n.title for n in imported_notes}
        assert titles == {"Duplicate"}

    def test_special_characters_round_trip(self, test_db: Session, test_user):
        # 1. Create note with special characters in title
        title = r"Title with / and \ and * and ?"
        body = "<p>Body Content</p>"
        root_folder = NotesFolderService.get_root_folder(test_db, user_id=test_user.id)
        note = NoteService.create_note(
            test_db,
            test_user.id,
            NoteCreateSchema(title=title, body=body, folder_id=root_folder.id)
        )

        # 2. Export to HTML
        content, filename = NotesExportService.export_single_note(test_db, test_user.id, note.id, ExportType.HTML)
        # filename should be sanitized: "Title with   and   and   and  .html" (multiple spaces) or similar
        # Actually _generate_export_filename uses: ''.join([char for char in note.title if char.isalnum()
        # or char in (' ', '.', '_')]).rstrip()
        assert "/" not in filename
        assert "*" not in filename

        # 3. Import back
        import_folder = NotesFolderService.create_import_folder(test_db, test_user.id)
        imported_note = NotesImportService.import_file(
            test_db,
            test_user.id,
            filename,
            content.encode('utf-8'),
            import_folder.id
        )

        # 4. Verify
        assert imported_note is not None
        # Title will be the sanitized filename (without extension)
        # Note: ExportService adds <h1>Original Title</h1>, so ImportService should extract it correctly!
        assert imported_note.title == title
        assert imported_note.body.strip() == body.strip()

from enum import Enum


class NotesFolderType(str, Enum):
    REGULAR = 'regular'
    ROOT = 'root'
    TRASH = 'trash'


class ExportType(str, Enum):
    MARKDOWN = 'markdown'
    HTML = 'html'
    PDF = 'pdf'


class ExportTarget(str, Enum):
    SINGLE_NOTE = 'single_note'
    FOLDER_NOTES = 'folder_notes'
    ALL_NOTES = 'all_notes'


EXPORT_TYPE_EXTENSION_MAP = {
    ExportType.MARKDOWN: 'md',
    ExportType.HTML: 'html',
    ExportType.PDF: 'pdf',
}


EXPORT_MEDIA_TYPE_MAP = {
    ExportType.MARKDOWN: 'text/markdown',
    ExportType.HTML: 'text/html',
    ExportType.PDF: 'application/pdf',
}

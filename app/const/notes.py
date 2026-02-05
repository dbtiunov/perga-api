from enum import Enum


class NotesFolderType(str, Enum):
    REGULAR = "regular"
    TRASH = "trash"
    ARCHIVE = "archive"

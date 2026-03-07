from enum import Enum


class NotesFolderType(str, Enum):
    REGULAR = "regular"
    ROOT = "root"
    TRASH = "trash"

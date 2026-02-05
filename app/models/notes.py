from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.const.notes import NotesFolderType
from app.models.base import BaseModel

__all__ = (
    'NotesFolder',
    'Note',
)


class NotesFolder(BaseModel):
    __tablename__ = 'notes_folders'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey('notes_folders.id'), nullable=True, index=True)
    name = Column(String(length=256), nullable=False)
    index = Column(Integer, nullable=False, default=0)
    folder_type = Column(String(length=256), nullable=False, default=NotesFolderType.REGULAR)

    # Relationships
    user = relationship('User', back_populates='notes_folders')
    notes = relationship('Note', back_populates='folder')
    parent = relationship('NotesFolder', remote_side='NotesFolder.id', back_populates='subfolders')
    subfolders = relationship('NotesFolder', back_populates='parent', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NotesFolder(id={self.id}, name={self.name!r}, user_id={self.user_id})>"


class Note(BaseModel):
    __tablename__ = 'notes'

    title = Column(String(length=256), nullable=True)
    body = Column(Text, nullable=False, default='')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    index = Column(Integer, nullable=False, default=0)
    folder_id = Column(Integer, ForeignKey('notes_folders.id'), nullable=True, index=True)

    # Relationships
    user = relationship('User', back_populates='notes')
    folder = relationship('NotesFolder', back_populates='notes')

    def __repr__(self):
        return f"<Note(id={self.id}, title={self.title!r}, user_id={self.user_id})>"

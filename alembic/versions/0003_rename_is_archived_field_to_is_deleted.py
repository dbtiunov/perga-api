"""rename is_archived field to is_deleted

Revision ID: ca11bd4113f3
Revises: d78a87905eb3
Create Date: 2025-11-02 20:48:58.200533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ca11bd4113f3'
down_revision: Union[str, None] = 'd78a87905eb3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tables = ['planner_agenda_items', 'planner_agendas', 'planner_day_items', 'users']
    for table in tables:
        op.execute(f'ALTER TABLE {table} RENAME COLUMN is_archived TO is_deleted;')
        op.execute(f'ALTER TABLE {table} RENAME COLUMN archived_dt TO deleted_dt;')


def downgrade() -> None:
    tables = ['planner_agenda_items', 'planner_agendas', 'planner_day_items', 'users']
    for table in tables:
        op.execute(f'ALTER TABLE {table} RENAME COLUMN is_deleted TO is_archived;')
        op.execute(f'ALTER TABLE {table} RENAME COLUMN deleted_dt TO archived_dt;')

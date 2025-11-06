"""make deleted_dt timezone-aware (timestamptz)

Revision ID: e1a2b3c4d5f6
Revises: ca11bd4113f3
Create Date: 2025-11-04 18:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1a2b3c4d5f6'
down_revision: Union[str, None] = 'ca11bd4113f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure deleted_dt columns are timezone-aware (timestamptz)
    tables = ['planner_agenda_items', 'planner_agendas', 'planner_day_items', 'users']
    for table in tables:
        # Convert from timestamp without time zone to timestamptz, assuming stored values are UTC
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN deleted_dt TYPE TIMESTAMP WITH TIME ZONE "
            f"USING deleted_dt AT TIME ZONE 'UTC';"
        )


def downgrade() -> None:
    # Revert deleted_dt columns back to timestamp without time zone
    tables = ['planner_agenda_items', 'planner_agendas', 'planner_day_items', 'users']
    for table in tables:
        op.execute(
            f"ALTER TABLE {table} "
            f"ALTER COLUMN deleted_dt TYPE TIMESTAMP WITHOUT TIME ZONE "
            f"USING deleted_dt AT TIME ZONE 'UTC';"
        )

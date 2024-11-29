"""Agent instructions

Revision ID: 5fc0c7a0c865
Revises: 56c110bc4b05
Create Date: 2024-11-20 20:41:08.781821

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5fc0c7a0c865"
down_revision: str | None = "56c110bc4b05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agent",
        sa.Column("instructions", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent", "instructions")

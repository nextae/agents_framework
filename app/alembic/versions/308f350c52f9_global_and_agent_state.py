"""Global and agent state

Revision ID: 308f350c52f9
Revises: 56c110bc4b05
Create Date: 2024-11-09 23:06:58.112378

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "308f350c52f9"
down_revision: str | None = "56c110bc4b05"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    table = op.create_table(
        "globalstate",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.bulk_insert(table, [{"state": {}}])
    op.add_column(
        "agent",
        sa.Column("state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent", "state")
    op.drop_table("globalstate")

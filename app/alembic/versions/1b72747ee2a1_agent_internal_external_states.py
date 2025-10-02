"""Agent internal external states

Revision ID: 1b72747ee2a1
Revises: 475d1f131715
Create Date: 2025-10-02 23:35:49.829316

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "1b72747ee2a1"
down_revision: str | None = "475d1f131715"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("agent", "state", new_column_name="internal_state", nullable=False)
    op.add_column(
        "agent",
        sa.Column(
            "external_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("agent", "external_state")
    op.alter_column("agent", "internal_state", new_column_name="state", nullable=False)

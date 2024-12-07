"""Literal param type

Revision ID: 615891aa104e
Revises: 87f37185bb0c
Create Date: 2024-12-03 19:26:51.594801

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "615891aa104e"
down_revision: str | None = "87f37185bb0c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "actionparam",
        sa.Column(
            "literal_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("actionparam", "literal_values")

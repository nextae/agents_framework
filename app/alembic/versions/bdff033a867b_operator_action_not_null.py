"""Operator action not null

Revision ID: bdff033a867b
Revises: f4b1fec18782
Create Date: 2025-09-05 00:01:19.323551

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bdff033a867b"
down_revision: str | None = "f4b1fec18782"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "actionconditionoperator", "action_id", existing_type=sa.INTEGER(), nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "actionconditionoperator", "action_id", existing_type=sa.INTEGER(), nullable=True
    )

"""Unique action name

Revision ID: f4b1fec18782
Revises: 56df6d13bcc0
Create Date: 2025-02-04 19:36:42.862036

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4b1fec18782"
down_revision: str | None = "56df6d13bcc0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint("unique_action_name", "action", ["name"])


def downgrade() -> None:
    op.drop_constraint("unique_action_name", "action", type_="unique")

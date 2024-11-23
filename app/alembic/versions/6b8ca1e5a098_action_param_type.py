"""Action param type

Revision ID: 6b8ca1e5a098
Revises: 5fc0c7a0c865
Create Date: 2024-11-23 20:30:51.366485

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b8ca1e5a098"
down_revision: str | None = "5fc0c7a0c865"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "actionparam",
        sa.Column(
            "type",
            sa.Enum(
                "STRING",
                "INTEGER",
                "FLOAT",
                "BOOLEAN",
                name="actionparamtype",
                native_enum=False,
            ),
            nullable=False,
        ),
    )
    op.create_unique_constraint(
        "unique_action_id_name", "actionparam", ["action_id", "name"]
    )


def downgrade() -> None:
    op.drop_constraint("unique_action_id_name", "actionparam", type_="unique")
    op.drop_column("actionparam", "type")

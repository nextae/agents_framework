"""Players

Revision ID: 56df6d13bcc0
Revises: 95c20a6c12a4
Create Date: 2025-01-06 18:27:50.413021

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "56df6d13bcc0"
down_revision: str | None = "95c20a6c12a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "player",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column(
        "agentmessage",
        sa.Column("caller_player_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "agentmessage_caller_player_id_fkey",
        "agentmessage",
        "player",
        ["caller_player_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "agentmessage_caller_player_id_fkey", "agentmessage", type_="foreignkey"
    )
    op.drop_column("agentmessage", "caller_player_id")
    op.drop_table("player")

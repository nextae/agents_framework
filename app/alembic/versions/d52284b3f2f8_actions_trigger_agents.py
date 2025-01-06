"""Actions trigger agents

Revision ID: d52284b3f2f8
Revises: 615891aa104e
Create Date: 2024-12-25 18:44:05.533328

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d52284b3f2f8"
down_revision: str | None = "615891aa104e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "action", sa.Column("triggered_agent_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "action_triggered_agent_id_fkey",
        "action",
        "agent",
        ["triggered_agent_id"],
        ["id"],
    )
    op.add_column(
        "agentmessage", sa.Column("caller_agent_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "agentmessage_caller_agent_id_fkey",
        "agentmessage",
        "agent",
        ["caller_agent_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "agentmessage_caller_agent_id_fkey", "agentmessage", type_="foreignkey"
    )
    op.drop_column("agentmessage", "caller_agent_id")
    op.drop_constraint("action_triggered_agent_id_fkey", "action", type_="foreignkey")
    op.drop_column("action", "triggered_agent_id")

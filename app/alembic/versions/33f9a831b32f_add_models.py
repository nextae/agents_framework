"""Add models

Revision ID: 33f9a831b32f
Revises: 426a659ae62d
Create Date: 2024-11-04 18:36:55.026545

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "33f9a831b32f"
down_revision: str | None = "426a659ae62d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "actioncondition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "actionconditionmatch",
        sa.Column("action_id", sa.Integer(), nullable=False),
        sa.Column("condition_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["action_id"],
            ["action.id"],
        ),
        sa.ForeignKeyConstraint(
            ["condition_id"],
            ["actioncondition.id"],
        ),
        sa.PrimaryKeyConstraint("action_id", "condition_id"),
    )
    op.create_table(
        "agentmessage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("text_query", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "text_response",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("timestamp", sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "agentsactionsmatch",
        sa.Column("agent_id", sa.Integer(), nullable=False),
        sa.Column("action_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["action_id"],
            ["action.id"],
        ),
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["agent.id"],
        ),
        sa.PrimaryKeyConstraint("agent_id", "action_id"),
    )
    op.execute(
        """
        ALTER TABLE action
        ALTER COLUMN params TYPE JSONB
        USING params::jsonb;
        """
    )
    op.drop_column("action", "conditions")
    op.drop_column("agent", "conversation_history")


def downgrade() -> None:
    op.add_column(
        "agent",
        sa.Column(
            "conversation_history",
            sa.VARCHAR(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "action",
        sa.Column("conditions", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.alter_column(
        "action",
        "params",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.drop_table("agentsactionsmatch")
    op.drop_table("agentmessage")
    op.drop_table("actionconditionmatch")
    op.drop_table("actioncondition")

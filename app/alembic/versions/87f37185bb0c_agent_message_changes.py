"""Agent message changes

Revision ID: 87f37185bb0c
Revises: 308f350c52f9
Create Date: 2024-11-30 20:18:25.710560

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "87f37185bb0c"
down_revision: str | None = "308f350c52f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "agentmessage",
        sa.Column("query", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    )
    op.add_column(
        "agentmessage",
        sa.Column("response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.alter_column(
        "agentmessage",
        "timestamp",
        existing_type=postgresql.TIMESTAMP(),
        type_=sa.TIMESTAMP(timezone=True),
        existing_nullable=True,
    )
    op.drop_column("agentmessage", "text_query")
    op.drop_column("agentmessage", "text_response")


def downgrade() -> None:
    op.add_column(
        "agentmessage",
        sa.Column(
            "text_response",
            postgresql.JSONB(astext_type=sa.Text()),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "agentmessage",
        sa.Column("text_query", sa.VARCHAR(), autoincrement=False, nullable=False),
    )
    op.alter_column(
        "agentmessage",
        "timestamp",
        existing_type=sa.TIMESTAMP(timezone=True),
        type_=postgresql.TIMESTAMP(),
        existing_nullable=True,
    )
    op.drop_column("agentmessage", "response")
    op.drop_column("agentmessage", "query")

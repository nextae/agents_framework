"""Condition agent ID

Revision ID: 475d1f131715
Revises: bdff033a867b
Create Date: 2025-09-19 02:23:06.490071

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "475d1f131715"
down_revision: str | None = "bdff033a867b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("actioncondition", sa.Column("state_agent_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "actioncondition_state_agent_id_fkey",
        "actioncondition",
        "agent",
        ["state_agent_id"],
        ["id"],
    )

    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT id, state_variable_name FROM actioncondition"))
    for condition_id, state_variable_name in result.fetchall():
        prefix, trimmed_name = state_variable_name.split("/", 1)
        if prefix == "global":
            conn.execute(
                sa.text(
                    "UPDATE actioncondition SET state_variable_name = :name WHERE id = :id"
                ).bindparams(name=trimmed_name, id=condition_id)
            )
        else:
            agent_id = int(prefix.split("-")[1])
            conn.execute(
                sa.text(
                    """
                    UPDATE actioncondition SET
                       state_agent_id = :agent_id,
                       state_variable_name = :name
                    WHERE id = :id
                    """
                ).bindparams(agent_id=agent_id, name=trimmed_name, id=condition_id)
            )


def downgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id, state_variable_name, state_agent_id FROM actioncondition")
    )
    for condition_id, state_variable_name, state_agent_id in result.fetchall():
        if state_agent_id is not None:
            name = f"agent-{state_agent_id}/{state_variable_name}"
            conn.execute(
                sa.text(
                    "UPDATE actioncondition SET state_variable_name = :name WHERE id = :id"
                ).bindparams(name=name, id=condition_id)
            )
        else:
            name = f"global/{state_variable_name}"
            conn.execute(
                sa.text(
                    "UPDATE actioncondition SET state_variable_name = :name WHERE id = :id"
                ).bindparams(name=name, id=condition_id)
            )

    op.drop_constraint("actioncondition_state_agent_id_fkey", "actioncondition", type_="foreignkey")
    op.drop_column("actioncondition", "state_agent_id")

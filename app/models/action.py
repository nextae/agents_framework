from langchain_core.tools import Tool
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Integer, Relationship, SQLModel

from app.models.action_condition import ActionCondition
from app.models.actions_conditions_matches import ActionConditionMatches


class Action(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    name: str
    params: dict | None = Field(
        sa_column=Column(JSONB, nullable=True, default=None)
    )  # Or as empty dict?
    conditions: list[ActionCondition] = Relationship(link_model=ActionConditionMatches)
    description: str | None = Field(default=None, nullable=True)

    def to_tool(self) -> Tool:
        # Placeholder - not necessary?
        pass

    def to_structured_output(self):
        # Placeholder - not necessary?
        pass

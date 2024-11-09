from langchain_core.tools import Tool
from sqlmodel import Column, Field, Integer, Relationship, SQLModel

from app.models.action_condition import ActionCondition
from app.models.action_param import ActionParam
from app.models.actions_conditions_matches import ActionConditionMatches


class Action(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    name: str
    params: list[ActionParam] = Relationship()
    conditions: list[ActionCondition] = Relationship(link_model=ActionConditionMatches)
    description: str | None = Field(default=None, nullable=True)

    def to_tool(self) -> Tool:
        # Placeholder - not necessary?
        pass

    def to_structured_output(self):
        # Placeholder - not necessary?
        pass

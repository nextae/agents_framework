from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.action_condition_operator import ActionConditionOperator


class ComparisonMethod(str, Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    AT_LEAST = ">="
    AT_MOST = "<="


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class ActionConditionBase(SQLModel):
    parent_id: int = Field(foreign_key="actionconditionoperator.id")
    root_id: int = Field(foreign_key="actionconditionoperator.id")
    state_agent_id: int | None = Field(default=None, foreign_key="agent.id")
    state_variable_name: str
    comparison: ComparisonMethod = Field(
        sa_column=Column(SAEnum(ComparisonMethod, native_enum=False), nullable=False)
    )
    expected_value: str


class ActionCondition(ActionConditionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    parent: "ActionConditionOperator" = Relationship(
        back_populates="conditions",
        sa_relationship_kwargs={"foreign_keys": "[ActionCondition.parent_id]"},
    )
    root: "ActionConditionOperator" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[ActionCondition.root_id]"}
    )


class ActionConditionRequest(ActionConditionBase):
    pass


class ActionConditionUpdateRequest(SQLModel):
    parent_id: int | None = None
    root_id: int | None = None
    state_agent_id: int | None = None
    state_variable_name: str | None = None
    comparison: ComparisonMethod | None = None
    expected_value: str | None = None


class ActionConditionResponse(ActionConditionBase):
    id: int

from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class ActionConditionOperatorBase(SQLModel):
    logical_operator: LogicalOperator = Field(
        sa_column=Column(SAEnum(LogicalOperator, native_enum=False), nullable=False)
    )
    action_id: int = Field(nullable=True, foreign_key="action.id")


class ActionConditionOperator(ActionConditionOperatorBase, table=True):
    id: int = Field(default=None, primary_key=True)
    parent_id: int | None = Field(
        default=None, nullable=True, foreign_key="actionconditionoperator.id"
    )
    root_id: int = Field(
        default=None, nullable=True, foreign_key="actionconditionoperator.id"
    )

    def to_tree_node(self):
        from app.services.action_condition import ActionConditionTreeNode

        return ActionConditionTreeNode(self.id, self.logical_operator, None, None, None)

    def is_root(self) -> bool:
        return self.root_id == self.id


class ActionConditionOperatorRequest(ActionConditionOperatorBase):
    parent_id: int
    root_id: int


class NewConditionTreeRequest(ActionConditionOperatorBase):
    pass


class ActionConditionOperatorUpdateRequest(SQLModel):
    logical_operator: LogicalOperator | None = None
    action_id: int | None = None
    parent_id: int | None = None
    root_id: int | None = None


class ActionConditionOperatorResponse(ActionConditionOperatorBase):
    id: int
    parent_id: int | None
    root_id: int | None

from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class ActionConditionOperator(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    parent_id: int = Field(default=None, nullable=True)
    root_id: int
    logical_operator: LogicalOperator = Field(
        sa_column=Column(SAEnum(LogicalOperator, native_enum=False), nullable=False)
    )

    def to_tree_node(self):
        from app.services.action_condition import ActionConditionTreeNode

        return ActionConditionTreeNode(self.id, self.logical_operator, None, None, None)

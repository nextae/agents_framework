from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel


class ComparisonMethod(str, Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    AT_LEAST = ">="
    AT_MOST = "<="


class ActionCondition(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    parent_id: int = Field(foreign_key="actionconditionoperator.id")
    root_id: int = Field(foreign_key="actionconditionoperator.id")
    state_variable_name: str  # Foreign key to state or something?
    comparison: ComparisonMethod = Field(
        sa_column=Column(SAEnum(ComparisonMethod, native_enum=False), nullable=False)
    )
    expected_value: str

    def validate_condition(self):
        # TODO sometime in the future
        pass

    def to_tree_node(self):
        from app.services.action_condition import ActionConditionTreeNode

        return ActionConditionTreeNode(
            self.id,
            None,
            self.comparison,
            self.state_variable_name,
            self.expected_value,
        )

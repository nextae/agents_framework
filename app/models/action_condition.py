from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


class ComparisonMethod(str, Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    AT_LEAST = ">="
    AT_MOST = "<="


class ActionConditionBase(SQLModel):
    parent_id: int = Field(foreign_key="actionconditionoperator.id")
    root_id: int = Field(foreign_key="actionconditionoperator.id")
    state_variable_name: str
    comparison: ComparisonMethod = Field(
        sa_column=Column(SAEnum(ComparisonMethod, native_enum=False), nullable=False)
    )
    expected_value: str


class ActionCondition(ActionConditionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    async def validate_condition(self, db: AsyncSession) -> bool:
        tree_node = self.to_tree_node()
        return await tree_node.validate_leaf(db)

    def to_tree_node(self):
        from app.services.action_condition import ActionConditionTreeNode

        return ActionConditionTreeNode(
            self.id,
            None,
            self.comparison,
            self.state_variable_name,
            self.expected_value,
        )


class ActionConditionRequest(ActionConditionBase):
    pass


class ActionConditionUpdateRequest(SQLModel):
    parent_id: int | None = None
    root_id: int | None = None
    state_variable_name: str | None = None
    comparison: ComparisonMethod | None = None
    expected_value: str | None = None


class ActionConditionResponse(ActionConditionBase):
    id: int

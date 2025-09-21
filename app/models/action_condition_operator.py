from typing import Optional

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, Relationship, SQLModel

from app.models.action_condition import ActionCondition, LogicalOperator


class ActionConditionOperatorBase(SQLModel):
    logical_operator: LogicalOperator = Field(
        sa_column=Column(SAEnum(LogicalOperator, native_enum=False), nullable=False)
    )
    action_id: int = Field(nullable=False, foreign_key="action.id")


class ActionConditionOperator(ActionConditionOperatorBase, table=True):
    id: int = Field(default=None, primary_key=True)
    parent_id: int | None = Field(
        default=None, nullable=True, foreign_key="actionconditionoperator.id"
    )
    root_id: int = Field(default=None, nullable=True, foreign_key="actionconditionoperator.id")

    conditions: list[ActionCondition] = Relationship(
        back_populates="parent",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "[ActionCondition.parent_id]"},
    )
    operators: list["ActionConditionOperator"] = Relationship(
        back_populates="parent",
        cascade_delete=True,
        sa_relationship_kwargs={"foreign_keys": "[ActionConditionOperator.parent_id]"},
    )
    parent: Optional["ActionConditionOperator"] = Relationship(
        back_populates="operators",
        sa_relationship_kwargs={
            "remote_side": "ActionConditionOperator.id",
            "foreign_keys": "[ActionConditionOperator.parent_id]",
        },
    )

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

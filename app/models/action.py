from typing import TYPE_CHECKING

from pydantic import BaseModel, create_model
from sqlmodel import Field, Relationship, SQLModel

from app.models.action_condition_operator import ActionConditionOperator
from app.models.action_param import ActionParam, ActionParamResponse
from app.models.actions_conditions_match import ActionConditionMatch
from app.models.agents_actions_match import AgentsActionsMatch

if TYPE_CHECKING:
    from app.models import Agent


class ActionBase(SQLModel):
    name: str
    description: str | None = None


class Action(ActionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    params: list[ActionParam] = Relationship(cascade_delete=True)
    conditions: list[ActionConditionOperator] = Relationship(
        link_model=ActionConditionMatch
    )
    agents: list["Agent"] = Relationship(
        back_populates="actions", link_model=AgentsActionsMatch
    )

    def to_structured_output(self) -> type[BaseModel]:
        """Converts the action to a structured output model."""

        return create_model(
            self.name,
            **{
                param.name: (
                    param.python_type,
                    Field(..., description=param.description),
                )
                for param in self.params
            },
        )


class ActionRequest(ActionBase):
    pass


class ActionUpdateRequest(SQLModel):
    name: str | None = None
    description: str | None = None


class ActionResponse(ActionBase):
    id: int
    params: list[ActionParamResponse]
    conditions: list[ActionConditionOperator]  # Not sure what to return

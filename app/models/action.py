from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, create_model
from sqlmodel import Field, Relationship, SQLModel

from app.models.action_condition import ActionCondition
from app.models.action_param import ActionParam, ActionParamResponse
from app.models.actions_conditions_match import ActionConditionMatch
from app.models.agents_actions_match import AgentsActionsMatch

if TYPE_CHECKING:
    from app.models import Agent


class ActionBase(SQLModel):
    name: str
    triggered_agent_id: int | None = None
    description: str | None = None


class Action(ActionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    triggered_agent_id: int | None = Field(default=None, foreign_key="agent.id")

    triggered_agent: Optional["Agent"] = Relationship()
    params: list[ActionParam] = Relationship(cascade_delete=True)
    conditions: list[ActionCondition] = Relationship(link_model=ActionConditionMatch)
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
    triggered_agent_id: int | None = None
    name: str | None = None
    description: str | None = None


class ActionResponse(ActionBase):
    id: int
    params: list[ActionParamResponse]
    conditions: list[ActionCondition]

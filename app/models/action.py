from pydantic import BaseModel, create_model
from sqlmodel import Field, Relationship, SQLModel

from app.models.action_condition import ActionCondition
from app.models.action_param import ActionParam, ActionParamResponse
from app.models.actions_conditions_match import ActionConditionMatch


class ActionBase(SQLModel):
    name: str
    description: str | None = None


class Action(ActionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    params: list[ActionParam] = Relationship()
    conditions: list[ActionCondition] = Relationship(link_model=ActionConditionMatch)

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
    conditions: list[ActionCondition]

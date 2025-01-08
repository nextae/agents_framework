from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, create_model
from sqlmodel import Field, Relationship, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.action_param import ActionParam, ActionParamResponse
from app.models.agents_actions_match import AgentsActionsMatch

if TYPE_CHECKING:
    from app.models import Agent
    from app.services.action_condition import ActionConditionTreeNode


class ActionBase(SQLModel):
    name: str
    triggered_agent_id: int | None = None
    description: str | None = None


class Action(ActionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    triggered_agent_id: int | None = Field(default=None, foreign_key="agent.id")

    triggered_agent: Optional["Agent"] = Relationship()
    params: list[ActionParam] = Relationship(cascade_delete=True)
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

    async def __get_condition_tree(
        self, db: AsyncSession
    ) -> "ActionConditionTreeNode | None":
        from app.services.action_condition import ActionConditionService

        conditions = await ActionConditionService.get_all_conditions_by_action_id(
            self.id, db
        )
        if not conditions:
            return None

        tree = ActionConditionService.build_condition_tree(conditions)
        return tree

    async def evaluate_conditions(self, db: AsyncSession) -> bool:
        tree = await self.__get_condition_tree(db)
        return await tree.evaluate_tree(db) if tree else True


class ActionRequest(ActionBase):
    pass


class ActionUpdateRequest(SQLModel):
    triggered_agent_id: int | None = None
    name: str | None = None
    description: str | None = None


class ActionResponse(ActionBase):
    id: int
    params: list[ActionParamResponse]

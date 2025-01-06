from pydantic import BaseModel, create_model
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.llm.chain import create_chain
from app.llm.models import ChainInput, ChainOutput
from app.models.action import Action, ActionResponse
from app.models.agent_message import AgentMessage
from app.models.agents_actions_match import AgentsActionsMatch
from app.models.global_state import State


class AgentBase(SQLModel):
    name: str
    description: str | None = None
    instructions: str | None = None


class Agent(AgentBase, table=True):
    id: int = Field(default=None, primary_key=True)
    state: State = Field(default={}, sa_column=Column(JSONB))

    conversation_history: list[AgentMessage] = Relationship(cascade_delete=True)
    actions: list[Action] = Relationship(
        back_populates="agents", link_model=AgentsActionsMatch
    )

    async def to_structured_output(self, db: AsyncSession) -> type[BaseModel]:
        """Creates a Pydantic model for the structured output of the agent."""

        actions_model = create_model(
            "Actions",
            **{
                action.name: (
                    action.to_structured_output() | None,
                    Field(..., description=action.description),
                )
                for action in self.actions
                if await action.evaluate_conditions(db)
            },
        )

        return create_model(
            "Response",
            response=(str, Field(..., description="The text response.")),
            actions=(actions_model, Field(..., description="The actions to take.")),
        )

    async def query(self, query: str, global_state: State, db) -> ChainOutput:
        """Queries the agent."""

        chain_input = ChainInput(
            query=query,
            instructions=self.instructions or "",
            global_state=global_state,
            agent_state=self.state,
        )
        chain = await create_chain(self, db)
        return await chain.ainvoke(chain_input)


class AgentRequest(AgentBase):
    pass


class AgentUpdateRequest(SQLModel):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None


class AgentResponse(AgentBase):
    id: int
    actions: list[ActionResponse]

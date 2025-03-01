from pydantic import BaseModel, create_model
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.llm.chain import create_chain
from app.llm.models import AgentDetails, ChainInput, ChainOutput
from app.models.action import Action, ActionResponse
from app.models.agent_message import AgentMessage
from app.models.agents_actions_match import AgentsActionsMatch
from app.models.global_state import State
from app.models.player import Player

CONVERSATION_HISTORY_PRIMARY_JOIN = """
or_(
    Agent.id == AgentMessage.agent_id,
    Agent.id == AgentMessage.caller_agent_id
)
"""


class AgentBase(SQLModel):
    name: str
    description: str | None = None
    instructions: str | None = None


class Agent(AgentBase, table=True):
    id: int = Field(default=None, primary_key=True)
    state: State = Field(default={}, sa_column=Column(JSONB))

    conversation_history: list[AgentMessage] = Relationship(
        back_populates="agent",
        cascade_delete=True,
        sa_relationship_kwargs={
            "primaryjoin": CONVERSATION_HISTORY_PRIMARY_JOIN,
            "order_by": "AgentMessage.timestamp",
        },
    )
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

    def to_details(self) -> AgentDetails:
        """Converts the agent to agent details dict."""

        return AgentDetails(
            agent_name=self.name,
            agent_id=self.id,
            agent_description=self.description or "",
        )

    async def query(
        self,
        query: str,
        caller: "Player | Agent",
        global_state: State,
        db: AsyncSession,
    ) -> ChainOutput:
        """Queries the agent."""

        chain_input = ChainInput(
            query=str({"caller": caller.to_details(), "query": query}),
            instructions=self.instructions or "",
            global_state=global_state,
            agent_state=self.state,
            action_agents={
                action.name: action.triggered_agent.to_details()
                for action in self.actions
                if action.triggered_agent is not None
            },
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

from pydantic import BaseModel, create_model
from sqlmodel import Field, Relationship, SQLModel

from app.llm.chain import create_chain
from app.llm.models import ChainOutput
from app.models.action import Action, ActionResponse
from app.models.agent_message import AgentMessage
from app.models.agents_actions_match import AgentsActionsMatch


class AgentBase(SQLModel):
    name: str
    description: str | None = None
    instructions: str | None = None


class Agent(AgentBase, table=True):
    id: int = Field(default=None, primary_key=True)

    conversation_history: list[AgentMessage] = Relationship(cascade_delete=True)
    actions: list[Action] = Relationship(
        back_populates="agents", link_model=AgentsActionsMatch
    )

    def to_structured_output(self) -> type[BaseModel]:
        """Creates a Pydantic model for the structured output of the agent."""

        actions_model = create_model(
            "Actions",
            **{
                action.name: (
                    action.to_structured_output() | None,
                    Field(..., description=action.description),
                )
                for action in self.actions
            },
        )

        return create_model(
            "Response",
            response=(str, Field(..., description="The text response.")),
            actions=(actions_model, Field(..., description="The actions to take.")),
        )

    async def query(self, query: str) -> ChainOutput:
        """Queries the agent."""

        chain = create_chain(self)
        return await chain.ainvoke({"query": query})


class AgentRequest(AgentBase):
    pass


class AgentUpdateRequest(SQLModel):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None


class AgentResponse(AgentBase):
    id: int
    conversation_history: list[AgentMessage]
    actions: list[ActionResponse]

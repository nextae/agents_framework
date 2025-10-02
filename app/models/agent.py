from functools import cached_property

from pydantic import create_model
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel

from app.llm.models import AgentDetails, ChainOutput
from app.models.action import Action, ActionResponse
from app.models.agent_message import AgentMessage
from app.models.agents_actions_match import AgentsActionsMatch
from app.models.global_state import State

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
    external_state: State = Field(default={}, sa_column=Column(JSONB, nullable=False))
    internal_state: State = Field(default={}, sa_column=Column(JSONB, nullable=False))

    conversation_history: list[AgentMessage] = Relationship(
        back_populates="agent",
        cascade_delete=True,
        sa_relationship_kwargs={
            "primaryjoin": CONVERSATION_HISTORY_PRIMARY_JOIN,
            "order_by": "AgentMessage.timestamp",
        },
    )
    actions: list[Action] = Relationship(
        back_populates="agents",
        link_model=AgentsActionsMatch,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @cached_property
    def combined_state(self) -> State:
        """
        Combine the internal and external state of the agent.
        In case of key conflicts, the internal state takes precedence.

        Returns:
            State: The combined state of the agent.
        """

        return self.external_state | self.internal_state

    def to_structured_output(self, available_actions: list[Action]) -> type[ChainOutput]:
        """
        Create a Pydantic model representing the structured output of the agent's response.

        Args:
            available_actions (list[Action]):
                The list of actions that have been evaluated and are available.

        Returns:
            type[ChainOutput]: The Pydantic model representing the structured output.
        """

        actions_model = create_model(
            "Actions",
            **{
                action.name: (
                    action.to_structured_output() | None,
                    Field(..., description=action.description),
                )
                for action in available_actions
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
            agent_external_state=self.external_state,
        )


class AgentRequest(AgentBase):
    pass


class AgentUpdateRequest(SQLModel):
    name: str | None = None
    description: str | None = None
    instructions: str | None = None


class AgentResponse(AgentBase):
    id: int
    actions: list[ActionResponse]

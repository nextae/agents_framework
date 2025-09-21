from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import TIMESTAMP, Column, Field, Relationship, SQLModel
from typing_extensions import TypedDict

if TYPE_CHECKING:
    from app.models import Agent, Player


class ActionResponseDict(TypedDict):
    name: str
    params: dict[str, Any]


class QueryResponseDict(TypedDict):
    response: str
    actions: list[ActionResponseDict]


class AgentMessage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    caller_agent_id: int | None = Field(default=None, foreign_key="agent.id")
    caller_player_id: int | None = Field(default=None, foreign_key="player.id")
    query: str
    response: QueryResponseDict = Field(sa_column=Column(JSONB))
    timestamp: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True)),
        default_factory=lambda: datetime.now(UTC),
    )

    agent: "Agent" = Relationship(
        back_populates="conversation_history",
        sa_relationship_kwargs={"foreign_keys": "[AgentMessage.agent_id]"},
    )

    def to_llm_messages(self, caller: Optional["Agent | Player"]) -> tuple[HumanMessage, AIMessage]:
        """
        Converts the agent message to LangChain LLM messages.

        Args:
            caller (Agent | Player): The caller of the message.

        Returns:
            tuple[HumanMessage, AIMessage]: The converted messages.
        """

        human_message = HumanMessage(
            content=str(
                {
                    "caller": caller.to_details() if caller is not None else "Unknown",
                    "query": self.query,
                }
            )
        )
        ai_message = AIMessage(content=str(self.response))
        return human_message, ai_message

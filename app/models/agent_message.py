from datetime import UTC, datetime
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import TIMESTAMP, Column, Field, SQLModel
from typing_extensions import TypedDict


class ActionResponseDict(TypedDict):
    name: str
    params: dict[str, Any]


class QueryResponseDict(TypedDict):
    response: str
    actions: list[ActionResponseDict]


class AgentMessage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="agent.id")
    query: str
    response: QueryResponseDict = Field(sa_column=Column(JSONB))
    timestamp: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True)),
        default_factory=lambda: datetime.now(UTC),
    )

    def to_llm_messages(self) -> tuple[HumanMessage, AIMessage]:
        """Converts the agent message to LangChain LLM messages."""

        human_message = HumanMessage(content=self.query)
        ai_message = AIMessage(content=str(self.response))
        return human_message, ai_message

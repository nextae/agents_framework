from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import TIMESTAMP, Column, Field, Integer, SQLModel


class AgentMessage(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))

    agent_id: int = Field(foreign_key="agent.id")
    text_query: str

    text_response: dict = Field(sa_column=Column(JSONB))

    timestamp: datetime = Field(
        sa_column=Column(TIMESTAMP), default_factory=lambda: datetime.now(UTC)
    )

    def parse(self, response):
        pass

    def to_json(self, response):
        pass

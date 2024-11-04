from sqlmodel import Column, Field, Integer, Relationship, SQLModel

from app.models.action import Action
from app.models.agent_message import AgentMessage
from app.models.agents_actions_matches import AgentsActionsMatches


class Agent(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    name: str
    description: str | None = Field(default=None, nullable=True)
    conversation_history: list[AgentMessage] = (
        Relationship()
    )  # AFAIU this should work :)
    actions: list[Action] = Relationship(link_model=AgentsActionsMatches)

from sqlmodel import Field, SQLModel


class AgentsActionsMatch(SQLModel, table=True):
    agent_id: int = Field(foreign_key="agent.id", primary_key=True)
    action_id: int = Field(foreign_key="action.id", primary_key=True)

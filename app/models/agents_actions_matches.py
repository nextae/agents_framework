from sqlmodel import Field, SQLModel


class AgentsActionsMatches(SQLModel, table=True):
    # id: int = Field(sa_column=Column(Integer, autoincrement=True, unique=True))
    agent_id: int = Field(foreign_key="agent.id", primary_key=True)
    action_id: int = Field(foreign_key="action.id", primary_key=True)

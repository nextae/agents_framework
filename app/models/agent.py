from sqlmodel import Field, SQLModel


class Agent(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, nullable=False)
    conversation_history: str | None = Field(default=None, nullable=True)
    description: str | None = Field(default=None, nullable=True)

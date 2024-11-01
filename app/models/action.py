from sqlmodel import Field, SQLModel


class Action(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(default=None, nullable=False)
    params: str | None = Field(default=None, nullable=False)
    conditions: str | None = Field(default=None, nullable=True)
    description: str | None = Field(default=None, nullable=True)

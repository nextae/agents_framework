from sqlmodel import Field, SQLModel


class ActionCondition(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    description: str | None = Field(default=None, nullable=True)  # Or maybe JSON?
    is_active: bool = Field(default=False, nullable=False)
    value: str | None = Field(default=None, nullable=True)

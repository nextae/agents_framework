from sqlmodel import Column, Field, Integer, SQLModel


class ActionCondition(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    name: str
    description: str | None = Field(default=None, nullable=True)  # Or maybe JSON?
    is_active: bool = Field(default=False, nullable=False)
    value: str | None = Field(default=None, nullable=True)

from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

StateValue = str | int | float | bool | dict | list | None


class GlobalState(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    state: dict[str, StateValue] = Field(sa_column=Column(JSONB))

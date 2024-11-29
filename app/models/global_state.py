from sqlalchemy import Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

StateValue = str | int | float | bool | dict | list | None
State = dict[str, StateValue]


class GlobalState(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    state: State = Field(sa_column=Column(JSONB))

from sqlmodel import Column, Field, Integer, SQLModel


class ActionParam(SQLModel, table=True):
    id: int = Field(sa_column=Column(Integer, autoincrement=True, primary_key=True))
    action_id: int = Field(foreign_key="action.id")
    name: str
    description: str

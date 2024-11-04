from sqlmodel import Field, SQLModel


class ActionConditionMatches(SQLModel, table=True):
    action_id: int = Field(foreign_key="action.id", primary_key=True)
    condition_id: int = Field(foreign_key="actioncondition.id", primary_key=True)

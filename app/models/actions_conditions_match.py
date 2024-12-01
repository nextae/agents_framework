from sqlmodel import Field, SQLModel


class ActionConditionMatch(SQLModel, table=True):
    action_id: int = Field(foreign_key="action.id", primary_key=True)
    condition_id: int = Field(
        foreign_key="actionconditionoperator.id", primary_key=True
    )

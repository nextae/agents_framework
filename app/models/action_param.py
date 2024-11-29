import enum

from sqlalchemy import Column, Enum, UniqueConstraint
from sqlmodel import Field, SQLModel


class ActionParamType(str, enum.Enum):
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"


PYTHON_TYPES = {
    ActionParamType.STRING: str,
    ActionParamType.INTEGER: int,
    ActionParamType.FLOAT: float,
    ActionParamType.BOOLEAN: bool,
}

ParamPythonType = type[str | int | float | bool]


class ActionParamBase(SQLModel):
    action_id: int
    name: str
    description: str
    type: ActionParamType


class ActionParam(ActionParamBase, table=True):
    id: int = Field(default=None, primary_key=True)
    action_id: int = Field(foreign_key="action.id")
    type: ActionParamType = Field(
        sa_column=Column(Enum(ActionParamType, native_enum=False), nullable=False),
    )

    __table_args__ = (
        UniqueConstraint("action_id", "name", name="unique_action_id_name"),
    )

    @property
    def python_type(self) -> ParamPythonType:
        """Gets the python type equivalent of the enum type."""

        return PYTHON_TYPES[self.type]


class ActionParamRequest(ActionParamBase):
    pass


class ActionParamUpdateRequest(SQLModel):
    action_id: int | None = None
    name: str | None = None
    description: str | None = None
    type: ActionParamType | None = None


class ActionParamResponse(ActionParamBase):
    id: int

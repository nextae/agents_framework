import enum
from typing import Literal, Self

from pydantic import model_validator
from sqlalchemy import Column, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class ActionParamType(str, enum.Enum):
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    LITERAL = "literal"


PYTHON_TYPES = {
    ActionParamType.STRING: str,
    ActionParamType.INTEGER: int,
    ActionParamType.FLOAT: float,
    ActionParamType.BOOLEAN: bool,
}

ParamPythonType = type[str | int | float | bool]
LiteralValue = str | float | int | bool | None


class ActionParamBase(SQLModel):
    action_id: int
    name: str
    description: str
    type: ActionParamType
    literal_values: list[LiteralValue] | None = None


class ActionParam(ActionParamBase, table=True):
    id: int = Field(default=None, primary_key=True)
    action_id: int = Field(foreign_key="action.id")
    type: ActionParamType = Field(
        sa_column=Column(Enum(ActionParamType, native_enum=False), nullable=False),
    )
    literal_values: list[LiteralValue] | None = Field(
        sa_column=Column(JSONB), default=None
    )

    __table_args__ = (
        UniqueConstraint("action_id", "name", name="unique_action_id_name"),
    )

    @property
    def python_type(self) -> ParamPythonType:
        """Gets the python type equivalent of the enum type."""

        if self.type == ActionParamType.LITERAL:
            return Literal[*self.literal_values]

        return PYTHON_TYPES[self.type]


class ActionParamRequest(ActionParamBase):
    @model_validator(mode="after")
    def validate_literal_values(self) -> Self:
        """Validates the literal values."""

        if self.type != ActionParamType.LITERAL and self.literal_values is not None:
            raise ValueError("Literal values are only allowed for the literal type")

        if self.type == ActionParamType.LITERAL and self.literal_values is None:
            raise ValueError("Literal values are required for the literal type")

        return self


class ActionParamUpdateRequest(ActionParamRequest):
    action_id: int | None = None
    name: str | None = None
    description: str | None = None
    type: ActionParamType | None = None
    literal_values: list[LiteralValue] | None = None


class ActionParamResponse(ActionParamBase):
    id: int

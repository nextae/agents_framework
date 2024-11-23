from typing import TypedDict

from pydantic import BaseModel


class ChainInput(TypedDict):
    query: str


class ChainOutput(BaseModel):
    response: str
    actions: BaseModel

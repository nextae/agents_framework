from typing import TypedDict

from pydantic import BaseModel

from app.models.global_state import State


class ChainInput(TypedDict):
    query: str
    instructions: str
    global_state: State
    agent_state: State


class ChainOutput(BaseModel):
    response: str
    actions: BaseModel

from typing import TypedDict

from pydantic import BaseModel

from app.models.global_state import State


class AgentDetails(TypedDict):
    agent_id: int
    agent_name: str
    agent_description: str
    agent_external_state: State


class PlayerDetails(TypedDict):
    player_id: int
    player_name: str
    player_description: str


class ChainInput(TypedDict):
    query: str
    instructions: str
    global_state: State
    agent_internal_state: State
    agent_external_state: State
    action_agents: dict[str, AgentDetails]


class ChainOutput(BaseModel):
    response: str
    actions: BaseModel

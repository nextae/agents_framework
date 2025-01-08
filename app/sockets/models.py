from typing import Any

from pydantic import BaseModel

from app.llm.models import ChainOutput
from app.models.global_state import State


class AgentQueryRequest(BaseModel):
    agent_id: int
    player_id: int
    query: str


class ActionQueryResponse(BaseModel):
    name: str
    params: dict[str, Any]


class AgentQueryResponse(BaseModel):
    response: str
    actions: list[ActionQueryResponse]

    @classmethod
    def from_llm_response(cls, llm_response: ChainOutput) -> "AgentQueryResponse":
        """Creates an AgentQueryResponse from an LLM response."""

        return cls(
            response=llm_response.response,
            actions=[
                ActionQueryResponse(name=action, params=params)
                for action, params in llm_response.actions.model_dump().items()
                if params is not None
            ],
        )


class UpdateStateRequest(BaseModel):
    state: State


class UpdateAgentStateRequest(BaseModel):
    agent_id: int
    state: State

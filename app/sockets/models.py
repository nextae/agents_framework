from typing import Any

from pydantic import BaseModel

from app.llm.models import ChainOutput
from app.models.global_state import State


class AgentQueryRequest(BaseModel):
    agent_id: int
    query: str


class ActionResponse(BaseModel):
    name: str
    params: dict[str, Any]


class AgentQueryResponse(BaseModel):
    agent_id: int
    response: str
    actions: list[ActionResponse]

    @classmethod
    def from_llm_response(
        cls, agent_id: int, llm_response: ChainOutput
    ) -> "AgentQueryResponse":
        """Creates an AgentQueryResponse from an LLM response."""

        return cls(
            agent_id=agent_id,
            response=llm_response.response,
            actions=[
                ActionResponse(name=action, params=params)
                for action, params in llm_response.actions.model_dump().items()
                if params is not None
            ],
        )


class UpdateStateRequest(BaseModel):
    state: State


class UpdateAgentStateRequest(BaseModel):
    agent_id: int
    state: State

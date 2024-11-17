from typing import Any

from pydantic import BaseModel

from app.models.global_state import StateValue


class AgentQueryRequest(BaseModel):
    agent_id: int
    query: str


class ActionResponse(BaseModel):
    name: str
    args: dict[str, Any]


class AgentQueryResponse(BaseModel):
    agent_id: int
    response: str
    actions: list[ActionResponse]

    @classmethod
    def from_llm_response(
        cls, agent_id: int, llm_response: BaseModel
    ) -> "AgentQueryResponse":
        """Creates an AgentQueryResponse from an LLM response."""

        return cls(
            agent_id=agent_id,
            response=llm_response.response,
            actions=[
                ActionResponse(name=action, args=args)
                for action, args in llm_response.actions.model_dump().items()
                if args is not None
            ],
        )


class UpdateStateRequest(BaseModel):
    state: dict[str, StateValue]


class UpdateAgentStateRequest(BaseModel):
    agent_id: int
    state: dict[str, StateValue]

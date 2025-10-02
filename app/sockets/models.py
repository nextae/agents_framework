from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, field_serializer

from app.llm.models import ChainOutput
from app.models import Agent
from app.models.agent_message import ActionResponseDict, QueryResponseDict
from app.models.global_state import State


class AgentQueryRequest(BaseModel):
    agent_id: int
    player_id: int
    query: str


class ActionQueryResponse(BaseModel):
    name: str
    params: dict[str, Any]
    triggered_agent_id: int | None = None

    def to_message_response(self) -> ActionResponseDict:
        return {
            "name": self.name,
            "params": self.params,
        }


class AgentQueryResponse(BaseModel):
    query_id: UUID
    agent_id: int
    response: str
    actions: list[ActionQueryResponse]

    @field_serializer("query_id")
    def serialize_query_id(self, value: UUID) -> str:
        return str(value)

    @classmethod
    def from_llm_response(cls, agent: Agent, llm_response: ChainOutput) -> "AgentQueryResponse":
        """Creates an AgentQueryResponse from an LLM response."""

        return cls(
            query_id=uuid4(),
            agent_id=agent.id,
            response=llm_response.response,
            actions=[
                ActionQueryResponse(
                    name=action,
                    params=params,
                    triggered_agent_id=next(
                        a for a in agent.actions if a.name == action
                    ).triggered_agent_id,
                )
                for action, params in llm_response.actions.model_dump().items()
                if params is not None
            ],
        )

    def to_message_response(self) -> QueryResponseDict:
        return {
            "response": self.response,
            "actions": [action.to_message_response() for action in self.actions],
        }


class UpdateStateRequest(BaseModel):
    state: State


class UpdateAgentStateRequest(BaseModel):
    agent_id: int
    state: State
    internal: bool


class AgentStateRequest(BaseModel):
    agent_id: int
    internal: bool


class AgentCombinedStateRequest(BaseModel):
    agent_id: int


class AuthPayload(BaseModel):
    access_token: str

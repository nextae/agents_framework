from typing import Any

from pydantic import BaseModel


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

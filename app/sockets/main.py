from typing import Any

import pydantic
import socketio

from ..db.database import Session
from ..services.agent import AgentService
from .models import AgentQueryRequest, AgentQueryResponse

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.on("query_agent")
async def query_agent(sid: str, data: Any) -> dict[str, Any]:
    """Queries an agent."""

    try:
        request = AgentQueryRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with Session() as db:
        agent = await AgentService.get_agent_by_id(request.agent_id, db)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found."}

    llm_response = await agent.query(request.query)

    response = AgentQueryResponse.from_llm_response(request.agent_id, llm_response)
    return response.model_dump()

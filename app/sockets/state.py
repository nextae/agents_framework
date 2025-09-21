from typing import Any

import pydantic

from app.repositories.unit_of_work import UnitOfWork
from app.services.agent_service import AgentService
from app.services.global_state_service import GlobalStateService

from .models import UpdateAgentStateRequest, UpdateStateRequest
from .server import sio


@sio.on("update_global_state")
async def update_global_state(sid: str, data: Any) -> dict[str, Any]:
    """Updates the global state."""

    try:
        request = UpdateStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        global_state = await GlobalStateService(uow).get_state()
        global_state.state = request.state
        await GlobalStateService(uow).update_state(global_state)

    return request.model_dump()


@sio.on("get_global_state")
async def get_global_state(sid: str) -> dict[str, Any]:
    """Gets the global state."""

    global_state = await GlobalStateService().get_state()
    return global_state.state


@sio.on("update_agent_state")
async def update_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Updates an Agent's state."""

    try:
        request = UpdateAgentStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        agent = await AgentService(uow).get_agent_by_id(request.agent_id)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found"}

        await AgentService(uow).update_agent_state(agent, request.state)

    return request.model_dump()


@sio.on("get_agent_state")
async def get_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Gets an Agent's state."""

    try:
        agent_id = int(data)
    except (ValueError, TypeError):
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        agent = await AgentService(uow).get_agent_by_id(agent_id)
        if agent is None:
            return {"error": f"Agent with id {agent_id} not found"}

    return agent.state

from typing import Any

import pydantic

from app.repositories.unit_of_work import UnitOfWork
from app.services.agent_service import AgentService
from app.services.global_state_service import GlobalStateService

from .models import (
    AgentCombinedStateRequest,
    AgentStateRequest,
    UpdateAgentStateRequest,
    UpdateStateRequest,
)
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

        if request.internal:
            agent.internal_state = request.state
        else:
            agent.external_state = request.state

        await uow.agents.update(agent)

    return request.model_dump()


@sio.on("get_agent_state")
async def get_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Gets an Agent's state."""

    try:
        request = AgentStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        agent = await AgentService(uow).get_agent_by_id(request.agent_id)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found"}

    return agent.internal_state if request.internal else agent.external_state


@sio.on("get_combined_agent_state")
async def get_combined_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Gets an Agent's combined state."""

    try:
        request = AgentCombinedStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        agent = await AgentService(uow).get_agent_by_id(request.agent_id)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found"}

    return agent.combined_state

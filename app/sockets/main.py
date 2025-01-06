from typing import Any

import pydantic
import socketio
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import Session
from app.models import Agent, GlobalState
from app.models.agent_message import AgentMessage
from app.services.agent import AgentService
from app.services.global_state import GlobalStateService

from .models import (
    AgentQueryRequest,
    AgentQueryResponse,
    UpdateAgentStateRequest,
    UpdateStateRequest,
)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.on("query_agent")
async def query_agent(sid: str, data: Any) -> dict[str, Any]:
    """Queries an agent."""

    try:
        request = AgentQueryRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with Session() as db:
        agent = await AgentService.get_agent_with_populated_actions(
            request.agent_id, db
        )
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found."}

        global_state = await GlobalStateService.get_state(db)

        llm_response = await agent.query(request.query, global_state.state, db)

        response = AgentQueryResponse.from_llm_response(llm_response)

        await sio.emit("agent_response", response.model_dump())
        message = AgentMessage(
            agent_id=agent.id,
            caller_agent_id=None,
            query=request.query,
            response=response.model_dump(),
        )

        await AgentService.add_agent_message(message, db)

        await _trigger_agents(agent, global_state, response, db)


async def _trigger_agents(
    agent: Agent,
    global_state: GlobalState,
    response: AgentQueryResponse,
    db: AsyncSession,
) -> None:
    """Trigger agents using BFS."""

    agents_to_trigger = []
    for action_response in response.actions:
        action = next(a for a in agent.actions if a.name == action_response.name)
        if action.triggered_agent_id is None:
            continue

        triggered_agent = await AgentService.get_agent_with_populated_actions(
            action.triggered_agent_id, db
        )

        print(f"Triggering agent {triggered_agent.name} from action {action.name}")

        llm_response = await triggered_agent.query_from_action(
            action_response, agent, global_state.state, db
        )

        response = AgentQueryResponse.from_llm_response(llm_response)

        await sio.emit("agent_response", response.model_dump())
        message = AgentMessage(
            agent_id=triggered_agent.id,
            caller_agent_id=agent.id,
            query=str(action_response.params),
            response=response.model_dump(),
        )

        await AgentService.add_agent_message(message, db)

        agents_to_trigger.append((triggered_agent, response))

    for agent, response in agents_to_trigger:
        await _trigger_agents(agent, global_state, response, db)


@sio.on("update_global_state")
async def update_global_state(sid: str, data: Any) -> dict[str, Any]:
    """Updates the global state."""

    try:
        request = UpdateStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with Session() as db:
        global_state = await GlobalStateService.get_state(db)
        global_state.state = request.state
        await GlobalStateService.update_state(global_state, db)

    return request.model_dump()


@sio.on("update_agent_state")
async def update_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Updates an Agent's state."""

    try:
        request = UpdateAgentStateRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with Session() as db:
        agent = await AgentService.get_agent_by_id(request.agent_id, db)
        if agent is None:
            return {"error": "Agent not found."}

        await AgentService.update_agent_state(agent, request.state, db)

    return request.model_dump()

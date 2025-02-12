import logging
from typing import Any
from uuid import UUID

import pydantic
import socketio
from socketio import exceptions
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.auth import decode_access_token
from app.core.database import Session
from app.errors.conditions import ConditionEvaluationError
from app.models import Agent, GlobalState
from app.models.agent_message import AgentMessage
from app.services.agent import AgentService
from app.services.global_state import GlobalStateService
from app.services.player import PlayerService

from .models import (
    AgentQueryRequest,
    AgentQueryResponse,
    AuthPayload,
    UpdateAgentStateRequest,
    UpdateStateRequest,
)

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.on("connect")
async def authenticate(
    sid: str, _environ: dict[str, Any], auth: dict[str, str]
) -> None:
    """Handles connection and authentication of a client."""

    try:
        auth_payload = AuthPayload.model_validate(auth)
    except pydantic.ValidationError:
        logger.info(f"Socket client {sid} provided invalid auth payload")
        raise exceptions.ConnectionRefusedError("Invalid auth payload")

    if decode_access_token(auth_payload.access_token) is None:
        logger.info(f"Socket client {sid} provided invalid or expired access token")
        raise exceptions.ConnectionRefusedError("Invalid or expired access token")

    logger.info(f"Socket client connected: {sid}")


@sio.on("query_agent")
async def query_agent(sid: str, data: Any) -> dict[str, Any]:
    """Queries an agent."""

    try:
        request = AgentQueryRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with Session() as db:
        agent = await AgentService.get_populated_agent(request.agent_id, db)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found."}

        player = await PlayerService.get_player_by_id(request.player_id, db)
        if player is None:
            return {"error": f"Player with id {request.player_id} not found."}

        global_state = await GlobalStateService.get_state(db)

        try:
            llm_response = await agent.query(
                request.query, player, global_state.state, db
            )
        except ConditionEvaluationError as e:
            await sio.emit(
                "agent_response_error", {"error": f"Condition evaluation error: {e}"}
            )
            return {"success": False}
        except Exception as e:
            logger.exception(e)
            await sio.emit(
                "agent_response_error", {"error": f"Internal server error: {e}"}
            )
            return {"success": False}

        response = AgentQueryResponse.from_llm_response(agent, llm_response)

        await sio.emit("agent_response", response.model_dump())
        message = AgentMessage(
            agent_id=agent.id,
            caller_player_id=player.id,
            query=request.query,
            response=response.to_message_response(),
        )

        await AgentService.add_agent_message(message, db)

        result = await _trigger_agents(
            response.query_id, agent, global_state, response, db
        )

    await sio.emit("agent_response_end", {"query_id": str(response.query_id)})
    return {"success": result}


async def _trigger_agents(
    query_id: UUID,
    agent: Agent,
    global_state: GlobalState,
    response: AgentQueryResponse,
    db: AsyncSession,
) -> bool:
    """
    Triggers agents recursively.
    Returns whether all agents were triggered successfully.
    """

    agents_to_trigger = []
    for action_response in response.actions:
        action = next(a for a in agent.actions if a.name == action_response.name)
        if action.triggered_agent_id is None:
            continue

        triggered_agent = await AgentService.get_populated_agent(
            action.triggered_agent_id, db
        )
        if triggered_agent is None:
            logger.warning(f"Agent with id {action.triggered_agent_id} not found.")
            continue

        logger.debug(
            f"Triggering agent {triggered_agent.name} from action {action.name}"
        )

        try:
            llm_response = await triggered_agent.query(
                str(action_response.params), agent, global_state.state, db
            )
        except ConditionEvaluationError as e:
            await sio.emit(
                "agent_response_error", {"error": f"Condition evaluation error: {e}"}
            )
            return False
        except Exception as e:
            logger.exception(e)
            await sio.emit(
                "agent_response_error", {"error": f"Internal server error: {e}"}
            )
            return False

        response = AgentQueryResponse.from_llm_response(triggered_agent, llm_response)
        response.query_id = query_id

        await sio.emit("agent_response", response.model_dump())
        message = AgentMessage(
            agent_id=triggered_agent.id,
            caller_agent_id=agent.id,
            query=str(action_response.params),
            response=response.to_message_response(),
        )

        await AgentService.add_agent_message(message, db)

        agents_to_trigger.append((triggered_agent, response))

    results = [
        await _trigger_agents(query_id, agent, global_state, response, db)
        for agent, response in agents_to_trigger
    ]
    return all(results)


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


@sio.on("get_global_state")
async def get_global_state(sid: str) -> dict[str, Any]:
    """Gets the global state."""

    async with Session() as db:
        global_state = await GlobalStateService.get_state(db)

    return global_state.state


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


@sio.on("get_agent_state")
async def get_agent_state(sid: str, data: Any) -> dict[str, Any]:
    """Gets an Agent's state."""

    try:
        agent_id = int(data)
    except ValueError:
        return {"error": "Validation error."}

    async with Session() as db:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            return {"error": "Agent not found."}

    return agent.state

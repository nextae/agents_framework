import logging
from typing import Any
from uuid import UUID

import pydantic

from app.errors.conditions import ConditionEvaluationError
from app.models import Agent, GlobalState
from app.models.agent_message import AgentMessage
from app.repositories.unit_of_work import UnitOfWork
from app.services.agent_service import AgentService
from app.services.global_state_service import GlobalStateService
from app.services.llm_service import LLMService
from app.services.player_service import PlayerService

from .models import AgentQueryRequest, AgentQueryResponse
from .server import sio

logger = logging.getLogger(__name__)


@sio.on("query_agent")
async def query_agent(sid: str, data: Any) -> dict[str, Any]:
    """Queries an agent."""

    try:
        request = AgentQueryRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    async with UnitOfWork() as uow:
        agent = await AgentService(uow).get_populated_agent(request.agent_id)
        if agent is None:
            return {"error": f"Agent with id {request.agent_id} not found"}

        player = await PlayerService(uow).get_player_by_id(request.player_id)
        if player is None:
            return {"error": f"Player with id {request.player_id} not found"}

        global_state = await GlobalStateService(uow).get_state()

        try:
            llm_response = await LLMService(uow).query_agent(
                agent, request.query, player, global_state.state
            )
        except ConditionEvaluationError as e:
            await sio.emit("agent_response_error", {"error": f"Condition evaluation error: {e}"})
            return {"success": False}
        except Exception as e:
            logger.exception(e)
            await sio.emit("agent_response_error", {"error": f"Internal server error: {e}"})
            return {"success": False}

        response = AgentQueryResponse.from_llm_response(agent, llm_response)

        await sio.emit("agent_response", response.model_dump())
        message = AgentMessage(
            agent_id=agent.id,
            caller_player_id=player.id,
            query=request.query,
            response=response.to_message_response(),
        )

        await AgentService(uow).add_agent_message(message)

        result = await _trigger_agents(response.query_id, agent, global_state, response, uow)

    await sio.emit("agent_response_end", {"query_id": str(response.query_id)})
    return {"success": result}


async def _trigger_agents(
    query_id: UUID,
    agent: Agent,
    global_state: GlobalState,
    response: AgentQueryResponse,
    uow: UnitOfWork,
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

        triggered_agent = await AgentService(uow).get_populated_agent(action.triggered_agent_id)
        if triggered_agent is None:
            logger.warning(
                f"Triggered agent with id {action.triggered_agent_id} not found. "
                f"This should never happen."
            )
            continue

        logger.debug(f"Triggering agent {triggered_agent.name} from action {action.name}")

        try:
            llm_response = await LLMService(uow).query_agent(
                triggered_agent, str(action_response.params), agent, global_state.state
            )
        except ConditionEvaluationError as e:
            await sio.emit("agent_response_error", {"error": f"Condition evaluation error: {e}"})
            return False
        except Exception as e:
            logger.exception(e)
            await sio.emit("agent_response_error", {"error": f"Internal server error: {e}"})
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

        await AgentService(uow).add_agent_message(message)

        agents_to_trigger.append((triggered_agent, response))

    results = [
        await _trigger_agents(query_id, agent, global_state, response, uow)
        for agent, response in agents_to_trigger
    ]
    return all(results)

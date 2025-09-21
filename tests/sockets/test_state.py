from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Agent
from app.services.agent_service import AgentService
from app.services.global_state_service import GlobalStateService
from app.sockets.models import UpdateAgentStateRequest, UpdateStateRequest
from app.sockets.state import (
    get_agent_state,
    get_global_state,
    update_agent_state,
    update_global_state,
)


@pytest.fixture(scope="module")
def sio() -> Generator[MagicMock, None, None]:
    with patch("app.sockets.state.sio") as mock_sio:
        mock_sio.emit = AsyncMock()
        yield mock_sio


async def test_update_global_state__success(sio, sid, cleanup_db):
    # given
    request = UpdateStateRequest(state={"key": "value"})

    # when
    response = await update_global_state(sid, request.model_dump())

    # then
    assert response == request.model_dump()
    global_state = await GlobalStateService().get_state()
    assert global_state.state == request.state


async def test_update_global_state__validation_error(sio, sid):
    # given
    payload = {"state": "invalid"}

    # when
    response = await update_global_state(sid, payload)

    # then
    assert response == {"error": "Validation error."}


async def test_get_global_state__success(sio, sid, cleanup_db):
    # given
    state = {"key": "value"}
    global_state = await GlobalStateService().get_state()
    global_state.state = state
    await GlobalStateService().update_state(global_state)

    # when
    response = await get_global_state(sid)

    # then
    assert response == state


async def test_update_agent_state__success(sio, sid, insert, cleanup_db):
    # given
    agent = Agent(name="Agent 1", state={"status": "idle"})
    agent = await insert(agent)

    request = UpdateAgentStateRequest(agent_id=agent.id, state={"status": "active"})

    # when
    response = await update_agent_state(sid, request.model_dump())

    # then
    assert response == request.model_dump()
    updated_agent = await AgentService().get_agent_by_id(agent.id)
    assert updated_agent is not None
    assert updated_agent.state == request.state


async def test_update_agent_state__agent_not_found(sio, sid):
    # given
    request = UpdateAgentStateRequest(agent_id=999, state={"key": "value"})

    # when
    response = await update_agent_state(sid, request.model_dump())

    # then
    assert response == {"error": f"Agent with id {request.agent_id} not found"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"agent_id": "invalid", "state": {"key": "value"}},
        {"agent_id": 1, "state": "invalid"},
    ],
)
async def test_update_agent_state__validation_error(sio, sid, payload):
    # when
    response = await update_agent_state(sid, payload)

    # then
    assert response == {"error": "Validation error."}


async def test_get_agent_state__success(sio, sid, insert, cleanup_db):
    # given
    agent = Agent(name="Agent 1", state={"key": "value"})
    agent = await insert(agent)

    # when
    response = await get_agent_state(sid, agent.id)

    # then
    assert response == agent.state


async def test_get_agent_state__agent_not_found(sio, sid):
    # when
    response = await get_agent_state(sid, 999)

    # then
    assert response == {"error": "Agent with id 999 not found"}


@pytest.mark.parametrize("agent_id", [None, "invalid"])
async def test_get_agent_state__validation_error(sio, sid, agent_id):
    # when
    response = await get_agent_state(sid, agent_id)

    # then
    assert response == {"error": "Validation error."}

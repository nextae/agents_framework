import pytest

from app.models import ActionParam, AgentMessage, Player
from app.models.action import Action
from app.models.action_param import ActionParamType
from app.models.agent import Agent, AgentRequest, AgentResponse, AgentUpdateRequest
from app.models.agent_message import QueryResponseDict
from app.services.agent_service import AgentService


async def test_get_agents__success(client, insert, cleanup_db):
    # given
    agents = [
        Agent(name="Agent 1", description="desc 1"),
        Agent(name="Agent 2", description="desc 2"),
    ]
    agents = await insert(*agents)

    # when
    response = await client.get("/agents")

    # then
    assert response.status_code == 200
    assert [Agent.model_validate(agent) for agent in response.json()] == agents


async def test_create_agent__success(client, cleanup_db):
    # given
    request = AgentRequest(name="Test Agent", description="desc", instructions="instructions")

    # when
    response = await client.post("/agents", json=request.model_dump())

    # then
    assert response.status_code == 201
    response_agent = AgentResponse.model_validate(response.json())
    assert response_agent.name == request.name
    assert response_agent.description == request.description
    assert response_agent.instructions == request.instructions


@pytest.mark.parametrize(
    "payload", [{}, {"name": 999}, {"description": "desc"}, {"name": "name", "description": 999}]
)
async def test_create_agent__unprocessable_entity(client, payload):
    # when
    response = await client.post("/agents", json=payload)

    # then
    assert response.status_code == 422


async def test_get_agent_by_id__success(client, insert, cleanup_db):
    # given
    agent = Agent(
        name="Agent",
        description="desc",
        instructions="instructions",
        actions=[
            Action(
                name="Action",
                params=[
                    ActionParam(
                        action_id=0,
                        name="param1",
                        description="desc1",
                        type=ActionParamType.STRING,
                    )
                ],
            )
        ],
    )
    agent = await insert(agent)

    # when
    response = await client.get(f"/agents/{agent.id}")

    # then
    assert response.status_code == 200
    assert Agent.model_validate(response.json()) == agent


async def test_get_agent_by_id__not_found(client, cleanup_db):
    # given
    agent_id = 999

    # when
    response = await client.get(f"/agents/{agent_id}")

    # then
    assert response.status_code == 404
    assert f"Agent with id {agent_id} not found" in response.text


async def test_get_agent_by_id__unprocessable_entity(client):
    # given
    agent_id = "invalid"

    # when
    response = await client.get(f"/agents/{agent_id}")

    # then
    assert response.status_code == 422


async def test_update_agent__success(client, insert, cleanup_db):
    # given
    agent = Agent(name="Old Name", description="Old Desc")
    agent = await insert(agent)
    request = AgentUpdateRequest(name="New Name", description="New Desc")

    # when
    response = await client.patch(f"/agents/{agent.id}", json=request.model_dump())

    # then
    assert response.status_code == 200
    updated_agent = Agent.model_validate(response.json())
    assert updated_agent.name == request.name
    assert updated_agent.description == request.description


async def test_update_agent__not_found(client, cleanup_db):
    # given
    agent_id = 999
    request = AgentUpdateRequest(name="New Name")

    # when
    response = await client.patch(f"/agents/{agent_id}", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Agent with id {agent_id} not found" in response.text


async def test_update_agent__unprocessable_entity(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent")
    agent = await insert(agent)
    request = {"name": 999}

    # when
    response = await client.patch(f"/agents/{agent.id}", json=request)

    # then
    assert response.status_code == 422


async def test_delete_agent__success(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent to Delete")
    agent = await insert(agent)

    # when
    response = await client.delete(f"/agents/{agent.id}")

    # then
    assert response.status_code == 204
    assert await AgentService().get_agent_by_id(agent.id) is None


async def test_delete_agent__not_found(client, cleanup_db):
    # given
    agent_id = 999

    # when
    response = await client.delete(f"/agents/{agent_id}")

    # then
    assert response.status_code == 204


async def test_delete_agent__has_trigger_actions(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent with Action")
    agent = await insert(agent)
    action = Action(name="Action", triggered_agent_id=agent.id)
    await insert(action)

    # when
    response = await client.delete(f"/agents/{agent.id}")

    # then
    assert response.status_code == 409
    assert f"Agent with id {agent.id} has existing trigger actions" in response.text


async def test_get_agent_messages__success(client, insert, cleanup_db):
    # given
    player = Player(name="Player")
    player = await insert(player)

    agent = Agent(name="Agent")
    agent = await insert(agent)

    message = AgentMessage(
        agent_id=agent.id,
        caller_agent_id=agent.id,
        caller_player_id=player.id,
        query="Hello",
        response=QueryResponseDict(
            response="Hello",
            actions=[],
        ),
    )
    message = await insert(message)

    # when
    response = await client.get(f"/agents/{agent.id}/messages")

    # then
    assert response.status_code == 200
    assert [AgentMessage.model_validate(msg) for msg in response.json()] == [message]


async def test_get_agent_messages__not_found(client, cleanup_db):
    # given
    agent_id = 999

    # when
    response = await client.get(f"/agents/{agent_id}/messages")

    # then
    assert response.status_code == 404
    assert f"Agent with id {agent_id} not found" in response.text


async def test_delete_agent_messages__success(client, insert, cleanup_db):
    # given
    player = Player(name="Player")
    player = await insert(player)
    agent = Agent(
        name="Agent",
        conversation_history=[
            AgentMessage(
                agent_id=0,
                caller_agent_id=0,
                caller_player_id=player.id,
                query="Hello",
                response=QueryResponseDict(
                    response="Hello",
                    actions=[],
                ),
            )
        ],
    )
    agent = await insert(agent)

    # when
    response = await client.delete(f"/agents/{agent.id}/messages")

    # then
    assert response.status_code == 204


async def test_delete_agent_messages__not_found(client, cleanup_db):
    # given
    agent_id = 999

    # when
    response = await client.delete(f"/agents/{agent_id}/messages")

    # then
    assert response.status_code == 204


async def test_assign_action_to_agent__success(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent")
    action = Action(name="Action")
    agent, action = await insert(agent, action)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/{action.id}/assign")

    # then
    assert response.status_code == 200
    agent.actions.append(action)
    assert Agent.model_validate(response.json()) == agent


async def test_assign_action_to_agent__agent_not_found(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    action = await insert(action)

    # when
    response = await client.post(f"/agents/999/actions/{action.id}/assign")

    # then
    assert response.status_code == 404
    assert "Agent with id 999 not found" in response.text


async def test_assign_action_to_agent__action_not_found(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent")
    agent = await insert(agent)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/999/assign")

    # then
    assert response.status_code == 404
    assert "Action with id 999 not found" in response.text


async def test_assign_action_to_agent__conflict(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    agent = Agent(name="Agent", actions=[action])
    agent = await insert(agent)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/{action.id}/assign")

    # then
    assert response.status_code == 409
    assert (
        f"Action with id {action.id} has already been assigned to agent with id {agent.id}"
        in response.text
    )


async def test_remove_action_from_agent__success(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    agent = Agent(name="Agent", actions=[action])
    agent = await insert(agent)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/{action.id}/remove")

    # then
    assert response.status_code == 200
    agent.actions.remove(action)
    assert Agent.model_validate(response.json()) == agent


async def test_remove_action_from_agent__agent_not_found(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    action = await insert(action)

    # when
    response = await client.post(f"/agents/999/actions/{action.id}/remove")

    # then
    assert response.status_code == 404
    assert "Agent with id 999 not found" in response.text


async def test_remove_action_from_agent__action_not_found(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent")
    agent = await insert(agent)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/999/remove")

    # then
    assert response.status_code == 404
    assert "Action with id 999 not found" in response.text


async def test_remove_action_from_agent__not_assigned(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent")
    action = Action(name="Action")
    agent, action = await insert(agent, action)

    # when
    response = await client.post(f"/agents/{agent.id}/actions/{action.id}/remove")

    # then
    assert response.status_code == 409
    assert (
        f"Action with id {action.id} hasn't been assigned to agent with id {agent.id}"
        in response.text
    )

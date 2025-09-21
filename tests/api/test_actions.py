import pytest

from app.models import Action, ActionParam, Agent, GlobalState
from app.models.action import (
    ActionEvaluationResult,
    ActionRequest,
    ActionResponse,
    ActionUpdateRequest,
)
from app.models.action_condition import ActionCondition, ComparisonMethod
from app.models.action_param import ActionParamType
from app.services.action_service import ActionService
from app.services.global_state_service import GlobalStateService


async def test_get_actions__success(client, insert, cleanup_db):
    # given
    actions = [
        Action(name="Action 1", description="desc 1"),
        Action(name="Action 2", description="desc 2"),
    ]
    actions = await insert(*actions)

    # when
    response = await client.get("/actions")

    # then
    assert response.status_code == 200
    assert [Action.model_validate(a) for a in response.json()] == actions


async def test_create_action__success(client, cleanup_db):
    # given
    request = ActionRequest(name="Test Action", description="desc")

    # when
    response = await client.post("/actions", json=request.model_dump())

    # then
    assert response.status_code == 201
    response_action = ActionResponse.model_validate(response.json())
    assert response_action.name == request.name
    assert response_action.description == request.description


async def test_create_action__duplicate_name(client, insert, cleanup_db):
    # given
    existing_action = Action(name="existing")
    request = ActionRequest(name="existing")
    await insert(existing_action)

    # when
    response = await client.post("/actions", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"Action with name {existing_action.name} already exists" in response.text


@pytest.mark.parametrize(
    "payload", [{}, {"name": 999}, {"description": "desc"}, {"name": "name", "description": 999}]
)
async def test_create_action__unprocessable_entity(client, payload):
    # when
    response = await client.post("/actions", json=payload)

    # then
    assert response.status_code == 422


async def test_create_action__triggered_agent__success(client, insert, cleanup_db):
    # given
    agent = Agent(name="Agent 1")
    agent = await insert(agent)
    request = ActionRequest(name="Action with Agent", triggered_agent_id=agent.id)

    # when
    response = await client.post("/actions", json=request.model_dump())

    # then
    assert response.status_code == 201
    response_action = ActionResponse.model_validate(response.json())
    assert response_action.triggered_agent_id == agent.id


async def test_create_action__triggered_agent__not_found(client, cleanup_db):
    # given
    request = ActionRequest(name="Action with Invalid Agent", triggered_agent_id=999)

    # when
    response = await client.post("/actions", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Agent with id {request.triggered_agent_id} not found" in response.text


async def test_get_action_by_id__success(client, insert, cleanup_db):
    # given
    action = Action(
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
    action = await insert(action)

    # when
    response = await client.get(f"/actions/{action.id}")

    # then
    assert response.status_code == 200
    assert Action.model_validate(response.json()) == action


async def test_get_action_by_id__not_found(client, cleanup_db):
    # given
    action_id = 999

    # when
    response = await client.get(f"/actions/{action_id}")

    # then
    assert response.status_code == 404
    assert f"Action with id {action_id} not found" in response.text


async def test_get_action_by_id__unprocessable_entity(client):
    # given
    action_id = "invalid"

    # when
    response = await client.get(f"/actions/{action_id}")

    # then
    assert response.status_code == 422


async def test_update_action__success(client, insert, cleanup_db):
    # given
    action = Action(name="Old Name", description="Old Desc")
    action = await insert(action)
    request = ActionUpdateRequest(name="New Name", description="New Desc")

    # when
    response = await client.patch(f"/actions/{action.id}", json=request.model_dump())

    # then
    assert response.status_code == 200
    updated_action = Action.model_validate(response.json())
    assert updated_action.name == request.name
    assert updated_action.description == request.description


async def test_update_action__not_found(client, cleanup_db):
    # given
    action_id = 999
    request = ActionUpdateRequest(name="New Name")

    # when
    response = await client.patch(f"/actions/{action_id}", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Action with id {action_id} not found" in response.text


async def test_update_action__duplicate_name(client, insert, cleanup_db):
    # given
    action1 = Action(name="Action 1")
    action2 = Action(name="Action 2")
    action1, action2 = await insert(action1, action2)
    request = ActionUpdateRequest(name="Action 1")

    # when
    response = await client.patch(f"/actions/{action2.id}", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"Action with name {request.name} already exists" in response.text


async def test_update_action__unprocessable_entity(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    action = await insert(action)
    request = {"name": 999}

    # when
    response = await client.patch(f"/actions/{action.id}", json=request)

    # then
    assert response.status_code == 422


async def test_update_action__triggered_agent__success(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    agent = Agent(name="Agent")
    action, agent = await insert(action, agent)
    request = ActionUpdateRequest(triggered_agent_id=agent.id)

    # when
    response = await client.patch(
        f"/actions/{action.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 200
    updated_action = Action.model_validate(response.json())
    assert updated_action.triggered_agent_id == agent.id


async def test_update_action__triggered_agent__not_found(client, insert, cleanup_db):
    # given
    action = Action(name="Action")
    action = await insert(action)
    request = ActionUpdateRequest(triggered_agent_id=999)

    # when
    response = await client.patch(f"/actions/{action.id}", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Agent with id {request.triggered_agent_id} not found" in response.text


async def test_delete_action__success(client, insert, cleanup_db):
    # given
    action = Action(name="Action to Delete")
    action = await insert(action)

    # when
    response = await client.delete(f"/actions/{action.id}")

    # then
    assert response.status_code == 204
    assert await ActionService().get_action_by_id(action.id) is None


async def test_delete_action__not_found(client, cleanup_db):
    # given
    action_id = 999

    # when
    response = await client.delete(f"/actions/{action_id}")

    # then
    assert response.status_code == 204


async def test_evaluate_action_conditions__no_conditions__success(client, insert, cleanup_db):
    # given
    action = Action(name="Action to Evaluate")
    action = await insert(action)

    # when
    response = await client.post(f"/actions/{action.id}/evaluate_conditions")

    # then
    assert response.status_code == 200
    evaluation_result = ActionEvaluationResult.model_validate(response.json())
    assert evaluation_result.action_id == action.id
    assert evaluation_result.result is True


@pytest.mark.parametrize("number_value", [5, 15])
async def test_evaluate_action_conditions__with_conditions__success(
    client, insert, root_operator, cleanup_db, number_value
):
    # given
    global_state = GlobalState(id=1, state={"number": number_value})
    await GlobalStateService().update_state(global_state)

    expected_value = 10
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="number",
        comparison=ComparisonMethod.GREATER,
        expected_value=str(expected_value),
    )
    await insert(condition)

    # when
    response = await client.post(f"/actions/{root_operator.action_id}/evaluate_conditions")

    # then
    assert response.status_code == 200
    evaluation_result = ActionEvaluationResult.model_validate(response.json())
    assert evaluation_result.action_id == root_operator.action_id
    assert evaluation_result.result == (number_value > expected_value)


async def test_evaluate_action_conditions__action_not_found(client, cleanup_db):
    # given
    action_id = 999

    # when
    response = await client.post(f"/actions/{action_id}/evaluate_conditions")

    # then
    assert response.status_code == 404
    assert f"Action with id {action_id} not found" in response.text


async def test_evaluate_action_conditions__variable_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="missing_var",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"some_value"',
    )
    await insert(condition)

    # when
    response = await client.post(f"/actions/{root_operator.action_id}/evaluate_conditions")

    # then
    assert response.status_code == 409
    assert f"State variable name '{condition.state_variable_name}' not found" in response.text


async def test_evaluate_action_conditions__invalid_comparison(
    client, insert, root_operator, cleanup_db
):
    # given
    global_state = GlobalState(id=1, state={"text": "hello"})
    await GlobalStateService().update_state(global_state)

    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="text",
        comparison=ComparisonMethod.AT_LEAST,
        expected_value="true",
    )
    await insert(condition)

    # when
    response = await client.post(f"/actions/{root_operator.action_id}/evaluate_conditions")

    # then
    assert response.status_code == 409
    assert (
        f"Comparison '{condition.comparison.name}' is not valid for values: "
        f"state_var=hello, expected_value=True" in response.text
    )

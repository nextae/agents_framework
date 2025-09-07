import pytest

from app.core.database import Session
from app.models import Action, ActionParam
from app.models.action_param import (
    ActionParamRequest,
    ActionParamResponse,
    ActionParamType,
    ActionParamUpdateRequest,
)
from app.services.action_param import ActionParamService


async def test_create_param__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    request = ActionParamRequest(
        action_id=action.id,
        name="Test Param",
        description="Test description",
        type=ActionParamType.STRING,
    )

    # when
    response = await client.post("/params", json=request.model_dump())

    # then
    assert response.status_code == 201
    param = ActionParamResponse.model_validate(response.json())
    assert param.name == request.name
    assert param.description == request.description
    assert param.type == request.type
    assert param.action_id == action.id


async def test_create_param__with_literal_type__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    request = ActionParamRequest(
        action_id=action.id,
        name="Test Param",
        description="Test description",
        type=ActionParamType.LITERAL,
        literal_values=["value1", "value2", 3],
    )

    # when
    response = await client.post("/params", json=request.model_dump())

    # then
    assert response.status_code == 201
    param = ActionParamResponse.model_validate(response.json())
    assert param.type == ActionParamType.LITERAL
    assert param.literal_values == request.literal_values


async def test_create_param__action_not_found(client, cleanup_db):
    # given
    request = ActionParamRequest(
        action_id=999,
        name="Test Param",
        description="Test description",
        type=ActionParamType.STRING,
    )

    # when
    response = await client.post("/params", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Action with id {request.action_id} not found" in response.text


async def test_create_param__invalid_literal_values(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    request = {
        "action_id": action.id,
        "name": "Test Param",
        "description": "Test description",
        "type": ActionParamType.LITERAL,
        "literal_values": None,
    }

    # when
    response = await client.post("/params", json=request)

    # then
    assert response.status_code == 422


async def test_create_param__unnecessary_literal_values(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    request = {
        "action_id": action.id,
        "name": "Test Param",
        "description": "Test description",
        "type": ActionParamType.STRING,
        "literal_values": ["value1", "value2"],
    }

    # when
    response = await client.post("/params", json=request)

    # then
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"action_id": 1},
        {"action_id": 1, "name": 999, "description": "desc", "type": ActionParamType.STRING},
    ],
)
async def test_create_param__unprocessable_entity(client, insert, payload):
    # when
    response = await client.post("/params", json=payload)

    # then
    assert response.status_code == 422


async def test_get_action_param_by_id__success(client, insert, cleanup_db):
    # given
    action = Action(
        name="Test Action",
        params=[
            ActionParam(
                action_id=0,
                name="Test Param",
                description="Test description",
                type=ActionParamType.STRING,
            )
        ],
    )
    action = await insert(action)
    param = action.params[0]

    # when
    response = await client.get(f"/params/{param.id}")

    # then
    assert response.status_code == 200
    assert ActionParam.model_validate(response.json()) == param


async def test_get_action_param_by_id__not_found(client, cleanup_db):
    # given
    param_id = 999

    # when
    response = await client.get(f"/params/{param_id}")

    # then
    assert response.status_code == 404
    assert f"ActionParam with id {param_id} not found" in response.text


async def test_get_action_param_by_id__unprocessable_entity(client):
    # given
    param_id = "invalid"

    # when
    response = await client.get(f"/params/{param_id}")

    # then
    assert response.status_code == 422


async def test_update_action_param__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    param = ActionParam(
        action_id=action.id,
        name="Old Name",
        description="Old Description",
        type=ActionParamType.STRING,
    )
    param = await insert(param)
    request = ActionParamUpdateRequest(
        name="New Name", description="New Description", type=ActionParamType.INTEGER
    )

    # when
    response = await client.patch(
        f"/params/{param.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 200
    updated_param = ActionParam.model_validate(response.json())
    assert updated_param.name == request.name
    assert updated_param.description == request.description
    assert updated_param.type == request.type
    assert updated_param.action_id == action.id


async def test_update_action_param__change_to_literal__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    param = ActionParam(
        action_id=action.id, name="Param", description="Description", type=ActionParamType.STRING
    )
    param = await insert(param)
    request = ActionParamUpdateRequest(
        type=ActionParamType.LITERAL, literal_values=["option1", "option2"]
    )

    # when
    response = await client.patch(
        f"/params/{param.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 200
    updated_param = ActionParam.model_validate(response.json())
    assert updated_param.type == ActionParamType.LITERAL
    assert updated_param.literal_values == request.literal_values


async def test_update_action_param__not_found(client, cleanup_db):
    # given
    param_id = 999
    request = ActionParamUpdateRequest(name="New Name")

    # when
    response = await client.patch(f"/params/{param_id}", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"ActionParam with id {param_id} not found" in response.text


async def test_update_action_param__invalid_request(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    param = ActionParam(
        action_id=action.id, name="Param", description="Description", type=ActionParamType.STRING
    )
    param = await insert(param)
    request = {"type": ActionParamType.LITERAL, "literal_values": None}

    # when
    response = await client.patch(f"/params/{param.id}", json=request)

    # then
    assert response.status_code == 422


async def test_delete_action_param__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)
    param = ActionParam(
        action_id=action.id,
        name="Param to Delete",
        description="Description",
        type=ActionParamType.STRING,
    )
    param = await insert(param)

    # when
    response = await client.delete(f"/params/{param.id}")

    # then
    assert response.status_code == 204
    async with Session() as db:
        assert await ActionParamService.get_action_param_by_id(param.id, db) is None


async def test_delete_action_param__not_found(client, cleanup_db):
    # given
    param_id = 999

    # when
    response = await client.delete(f"/params/{param_id}")

    # then
    assert response.status_code == 204

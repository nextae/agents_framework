# pytest app/tests/api/test_conditions.py
import pytest

from app.core.database import Session
from app.models import Action, GlobalState
from app.models.action_condition import (
    ActionCondition,
    ActionConditionRequest,
    ActionConditionResponse,
    ActionConditionUpdateRequest,
    ComparisonMethod,
)
from app.models.action_condition_operator import (
    ActionConditionOperator,
    ActionConditionOperatorRequest,
    ActionConditionOperatorResponse,
    ActionConditionOperatorUpdateRequest,
    LogicalOperator,
    NewConditionTreeRequest,
)
from app.services.action_condition import ActionConditionService

pytestmark = pytest.mark.asyncio(loop_scope="session")


async def test_create_action_condition__success(client, insert, root_operator, cleanup_db):
    # given
    global_state = GlobalState(id=1, state={"test": "test_value"})
    await insert(global_state)

    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 201
    condition = ActionConditionResponse.model_validate(response.json())
    assert condition.parent_id == request.parent_id
    assert condition.root_id == request.root_id
    assert condition.state_variable_name == request.state_variable_name
    assert condition.comparison == request.comparison
    assert condition.expected_value == request.expected_value


async def test_create_action_condition__parent_not_found(client, cleanup_db):
    # given
    request = ActionConditionRequest(
        parent_id=999,
        root_id=999,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Operator with id {request.parent_id} not found" in response.text


async def test_create_action_condition__root_not_found(client, insert, root_operator, cleanup_db):
    # given
    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=999,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Root with id {request.root_id} not found" in response.text


async def test_create_action_condition__invalid_root(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)

    parent = ActionConditionOperator(logical_operator=LogicalOperator.AND, action_id=action.id)
    root = ActionConditionOperator(logical_operator=LogicalOperator.OR, action_id=action.id)
    parent, root = await insert(parent, root)

    request = ActionConditionRequest(
        parent_id=parent.id,
        root_id=root.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"Operator with id {request.root_id} is not a root" in response.text


async def test_create_action_condition__invalid_condition__invalid_state_variable(
    client, insert, root_operator, cleanup_db
):
    # given
    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"State variable name '{request.state_variable_name}' is not valid" in response.text


async def test_create_action_condition__invalid_condition__agent_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    agent_id = 999
    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name=f"agent-{agent_id}/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"Agent with id {agent_id} not found" in response.text


async def test_create_action_condition__invalid_condition__variable_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert "State variable name 'global/test' not found" in response.text


async def test_create_action_condition__invalid_condition__invalid_comparison(
    client, insert, root_operator, cleanup_db
):
    # given
    state_var = 999
    expected_value = "string_instead_of_int"
    global_state = GlobalState(id=1, state={"test": state_var})
    await insert(global_state)

    request = ActionConditionRequest(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.GREATER,
        expected_value=f'"{expected_value}"',
    )

    # when
    response = await client.post("/conditions/condition", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == f"Comparison '{request.comparison.name}' is not valid for values: "
        f"state_var={state_var}, expected_value={expected_value}"
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"parent_id": 1},
        {
            "root_id": 1,
            "parent_id": 1,
            "state_variable_name": "global/test",
            "comparison": 1,
            "expected_value": '"test_value"',
        },
    ],
)
async def test_create_action_condition__unprocessable_entity(client, payload):
    # when
    response = await client.post("/conditions/condition", json=payload)

    # then
    assert response.status_code == 422


async def test_create_action_condition_operator__success(client, insert, root_operator, cleanup_db):
    # given
    request = ActionConditionOperatorRequest(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )

    # when
    response = await client.post("/conditions/operator", json=request.model_dump())

    # then
    assert response.status_code == 201
    operator = ActionConditionOperatorResponse.model_validate(response.json())
    assert operator.logical_operator == request.logical_operator
    assert operator.action_id == request.action_id
    assert operator.parent_id == request.parent_id
    assert operator.root_id == request.root_id


async def test_create_action_condition_operator__parent_not_found(client, cleanup_db):
    # given
    request = ActionConditionOperatorRequest(
        logical_operator=LogicalOperator.OR,
        parent_id=999,
        root_id=999,
        action_id=999,
    )

    # when
    response = await client.post("/conditions/operator", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Operator with id {request.parent_id} not found" in response.text


async def test_create_action_condition_operator__root_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    request = ActionConditionOperatorRequest(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=999,
        action_id=999,
    )

    # when
    response = await client.post("/conditions/operator", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Root with id {request.root_id} not found" in response.text


async def test_create_action_condition_operator__invalid_root(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)

    parent = ActionConditionOperator(logical_operator=LogicalOperator.AND, action_id=action.id)
    root = ActionConditionOperator(logical_operator=LogicalOperator.OR, action_id=action.id)
    parent, root = await insert(parent, root)

    request = ActionConditionOperatorRequest(
        logical_operator=LogicalOperator.OR,
        parent_id=parent.id,
        root_id=root.id,
        action_id=999,
    )

    # when
    response = await client.post("/conditions/operator", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert f"Operator with id {request.root_id} is not a root" in response.text


async def test_create_action_condition_operator__action_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    request = ActionConditionOperatorRequest(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=999,
    )

    # when
    response = await client.post("/conditions/operator", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Action with id {request.action_id} not found" in response.text


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"logical_operator": LogicalOperator.OR},
        {"parent_id": 1, "root_id": 1, "action_id": 1, "logical_operator": "invalid"},
    ],
)
async def test_create_action_condition_operator__unprocessable_entity(client, payload):
    # when
    response = await client.post("/conditions/operator", json=payload)

    # then
    assert response.status_code == 422


async def test_create_new_condition_tree__success(client, insert, cleanup_db):
    # given
    action = Action(name="Test Action")
    action = await insert(action)

    request = NewConditionTreeRequest(logical_operator=LogicalOperator.AND, action_id=action.id)

    # when
    response = await client.post("/conditions/tree", json=request.model_dump())

    # then
    assert response.status_code == 201
    operator = ActionConditionOperatorResponse.model_validate(response.json())
    assert operator.logical_operator == request.logical_operator
    assert operator.action_id == request.action_id
    assert operator.root_id == operator.id
    assert operator.parent_id is None


async def test_create_new_condition_tree__action_not_found(client, cleanup_db):
    # given
    request = NewConditionTreeRequest(logical_operator=LogicalOperator.AND, action_id=132)

    # when
    response = await client.post("/conditions/tree", json=request.model_dump())

    # then
    assert response.status_code == 404
    assert f"Action with id {request.action_id} not found" in response.text


async def test_create_new_condition_tree__action_already_has_root(
    client, insert, root_operator, cleanup_db
):
    # given
    request = NewConditionTreeRequest(
        logical_operator=LogicalOperator.OR, action_id=root_operator.action_id
    )

    # when
    response = await client.post("/conditions/tree", json=request.model_dump())

    # then
    assert response.status_code == 409
    assert (
        f"Action with id {root_operator.action_id} already has "
        f"root assigned with id {root_operator.id}" in response.text
    )


async def test_get_action_conditions__success(client, insert, root_operator, cleanup_db):
    # given
    conditions = [
        ActionCondition(
            parent_id=root_operator.id,
            root_id=root_operator.id,
            state_variable_name="global/test1",
            comparison=ComparisonMethod.EQUAL,
            expected_value='"value1"',
        ),
        ActionCondition(
            parent_id=root_operator.id,
            root_id=root_operator.id,
            state_variable_name="global/test2",
            comparison=ComparisonMethod.NOT_EQUAL,
            expected_value='"value2"',
        ),
    ]
    conditions = await insert(*conditions)

    # when
    response = await client.get("/conditions/condition")

    # then
    assert response.status_code == 200
    assert [ActionCondition.model_validate(c) for c in response.json()] == conditions


async def test_get_action_condition_operators__success(client, insert, root_operator, cleanup_db):
    # given
    operators = [
        ActionConditionOperator(
            logical_operator=LogicalOperator.AND,
            action_id=root_operator.action_id,
            parent_id=root_operator.id,
            root_id=root_operator.id,
        ),
        ActionConditionOperator(
            logical_operator=LogicalOperator.OR,
            action_id=root_operator.action_id,
            parent_id=root_operator.id,
            root_id=root_operator.id,
        ),
    ]
    operators = await insert(*operators)

    # when
    response = await client.get("/conditions/operator")

    # then
    assert response.status_code == 200
    assert [ActionConditionOperator.model_validate(o) for o in response.json()] == [
        root_operator
    ] + operators


async def test_get_action_condition_by_id__success(client, insert, root_operator, cleanup_db):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    # when
    response = await client.get(f"/conditions/condition/{condition.id}")

    # then
    assert response.status_code == 200
    assert ActionCondition.model_validate(response.json()) == condition


async def test_get_action_condition_by_id__not_found(client, cleanup_db):
    # given
    condition_id = 999

    # when
    response = await client.get(f"/conditions/condition/{condition_id}")

    # then
    assert response.status_code == 404
    assert f"Action condition with id {condition_id} not found" in response.text


async def test_get_action_condition_by_id__unprocessable_entity(client):
    # given
    condition_id = "invalid"

    # when
    response = await client.get(f"/conditions/condition/{condition_id}")

    # then
    assert response.status_code == 422


async def test_get_action_condition_operator_by_id__success(
    client, insert, root_operator, cleanup_db
):
    # when
    response = await client.get(f"/conditions/operator/{root_operator.id}")

    # then
    assert response.status_code == 200
    assert ActionConditionOperator.model_validate(response.json()) == root_operator


async def test_get_action_condition_operator_by_id__not_found(client, cleanup_db):
    # given
    operator_id = 999

    # when
    response = await client.get(f"/conditions/operator/{operator_id}")

    # then
    assert response.status_code == 404
    assert f"Action condition operator with id {operator_id} not found" in response.text


async def test_get_action_condition_operator_by_id__unprocessable_entity(client):
    # given
    operator_id = "invalid"

    # when
    response = await client.get(f"/conditions/operator/{operator_id}")

    # then
    assert response.status_code == 422


async def test_update_action_condition__success(client, insert, root_operator, cleanup_db):
    # given
    global_state = GlobalState(id=1, state={"old": "old_value", "new": "new_value"})
    await insert(global_state)

    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/old",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"old_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(
        state_variable_name="global/new",
        comparison=ComparisonMethod.NOT_EQUAL,
        expected_value='"new_value"',
    )

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 200
    updated_condition = ActionCondition.model_validate(response.json())
    assert updated_condition.state_variable_name == request.state_variable_name
    assert updated_condition.comparison == request.comparison
    assert updated_condition.expected_value == request.expected_value
    assert updated_condition.parent_id == condition.parent_id
    assert updated_condition.root_id == condition.root_id
    assert updated_condition.id == condition.id


async def test_update_action_condition__not_found(client):
    # given
    condition_id = 999
    request = ActionConditionUpdateRequest(state_variable_name="global/new")

    # when
    response = await client.patch(
        f"/conditions/condition/{condition_id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Condition with id {condition_id} not found" in response.text


async def test_update_action_condition__operator_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/old",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"old_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(parent_id=999)

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Operator with id {request.parent_id} not found" in response.text


async def test_update_action_condition__root_not_found(client, insert, root_operator, cleanup_db):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/old",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"old_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(root_id=999)

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Root with id {request.root_id} not found" in response.text


async def test_update_action_condition__invalid_root(client, insert, root_operator, cleanup_db):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/old",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"old_value"',
    )
    condition = await insert(condition)

    new_root = ActionConditionOperator(
        logical_operator=LogicalOperator.AND, action_id=root_operator.action_id
    )
    new_root = await insert(new_root)

    request = ActionConditionUpdateRequest(root_id=new_root.id)

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert f"Operator with id {request.root_id} is not a root" in response.text


async def test_update_condition__invalid_condition__invalid_state_variable(
    client, insert, root_operator, cleanup_db
):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(state_variable_name="invalid_state_variable")

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert f"State variable name '{request.state_variable_name}' is not valid" in response.text


async def test_update_condition__invalid_condition__agent_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    agent_id = 999
    request = ActionConditionUpdateRequest(state_variable_name=f"agent-{agent_id}/test")

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert f"Agent with id {agent_id} not found" in response.text


async def test_update_condition__invalid_condition__variable_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(state_variable_name="global/non_existent")

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert f"State variable name '{request.state_variable_name}' not found" in response.text


async def test_update_condition__invalid_condition__invalid_comparison(
    client, insert, root_operator, cleanup_db
):
    # given
    state_var = 999
    expected_value = "string_instead_of_int"
    global_state = GlobalState(id=1, state={"test": state_var})
    await insert(global_state)

    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    request = ActionConditionUpdateRequest(
        comparison=ComparisonMethod.GREATER, expected_value=f'"{expected_value}"'
    )

    # when
    response = await client.patch(
        f"/conditions/condition/{condition.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == f"Comparison '{request.comparison.name}' is not valid for values: "
        f"state_var={state_var}, expected_value={expected_value}"
    )


@pytest.mark.parametrize("payload", [{"state_variable_name": 999}])
async def test_update_action_condition__unprocessable_entity(client, payload):
    # when
    response = await client.patch("/conditions/condition/1", json=payload)

    # then
    assert response.status_code == 422


async def test_update_action_condition_operator__success(client, insert, root_operator, cleanup_db):
    # given
    operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    operator = await insert(operator)

    request = ActionConditionOperatorUpdateRequest(logical_operator=LogicalOperator.AND)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 200
    updated_operator = ActionConditionOperator.model_validate(response.json())
    assert updated_operator.logical_operator == request.logical_operator
    assert updated_operator.action_id == operator.action_id
    assert updated_operator.parent_id == operator.parent_id
    assert updated_operator.root_id == operator.root_id
    assert updated_operator.id == operator.id


async def test_update_action_condition_operator__not_found(client):
    # given
    operator_id = 999
    request = ActionConditionOperatorUpdateRequest(logical_operator=LogicalOperator.AND)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator_id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Operator with id {operator_id} not found" in response.text


async def test_update_action_condition_operator__operator_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    operator = await insert(operator)

    request = ActionConditionOperatorUpdateRequest(parent_id=999)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Operator with id {request.parent_id} not found" in response.text


async def test_update_action_condition_operator__root_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    operator = await insert(operator)

    request = ActionConditionOperatorUpdateRequest(root_id=999)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Root with id {request.root_id} not found" in response.text


async def test_update_action_condition_operator__invalid_root(
    client, insert, root_operator, cleanup_db
):
    # given
    operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    operator = await insert(operator)

    new_root = ActionConditionOperator(
        logical_operator=LogicalOperator.AND, action_id=root_operator.action_id
    )
    new_root = await insert(new_root)

    request = ActionConditionOperatorUpdateRequest(root_id=new_root.id)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 409
    assert f"Operator with id {request.root_id} is not a root" in response.text


async def test_update_action_condition_operator__action_not_found(
    client, insert, root_operator, cleanup_db
):
    # given
    operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    operator = await insert(operator)

    request = ActionConditionOperatorUpdateRequest(action_id=999)

    # when
    response = await client.patch(
        f"/conditions/operator/{operator.id}", json=request.model_dump(exclude_unset=True)
    )

    # then
    assert response.status_code == 404
    assert f"Action with id {request.action_id} not found" in response.text


@pytest.mark.parametrize("payload", [{"logical_operator": "invalid"}])
async def test_update_action_condition_operator__unprocessable_entity(client, payload):
    # when
    response = await client.patch("/conditions/operator/1", json=payload)

    # then
    assert response.status_code == 422


async def test_delete_action_condition__success(client, insert, root_operator, cleanup_db):
    # given
    condition = ActionCondition(
        parent_id=root_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    # when
    response = await client.delete(f"/conditions/condition/{condition.id}")

    # then
    assert response.status_code == 204
    async with Session() as db:
        assert await ActionConditionService.get_condition_by_id(condition.id, db) is None


async def test_delete_action_condition__not_found(client, cleanup_db):
    # given
    condition_id = 999

    # when
    response = await client.delete(f"/conditions/condition/{condition_id}")

    # then
    assert response.status_code == 204


async def test_delete_action_condition_operator__success(client, insert, root_operator, cleanup_db):
    # when
    response = await client.delete(f"/conditions/operator/{root_operator.id}")

    # then
    assert response.status_code == 204
    async with Session() as db:
        assert (
            await ActionConditionService.get_condition_operator_by_id(root_operator.id, db) is None
        )


async def test_delete_action_condition_operator__not_found(client, cleanup_db):
    # given
    operator_id = 999

    # when
    response = await client.delete(f"/conditions/operator/{operator_id}")

    # then
    assert response.status_code == 204


async def test_delete_tree_by_root_id__success(client, insert, root_operator, cleanup_db):
    # given
    child_operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    child_operator = await insert(child_operator)

    condition = ActionCondition(
        parent_id=child_operator.id,
        root_id=root_operator.id,
        state_variable_name="global/test",
        comparison=ComparisonMethod.EQUAL,
        expected_value='"test_value"',
    )
    condition = await insert(condition)

    # when
    response = await client.delete(f"/conditions/condition_tree/{root_operator.id}")

    # then
    assert response.status_code == 204
    async with Session() as db:
        assert (
            await ActionConditionService.get_condition_operator_by_id(root_operator.id, db) is None
        )
        assert (
            await ActionConditionService.get_condition_operator_by_id(child_operator.id, db) is None
        )
        assert await ActionConditionService.get_condition_by_id(condition.id, db) is None


async def test_delete_tree_by_root_id__not_root(client, insert, root_operator, cleanup_db):
    # given
    child_operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    child_operator = await insert(child_operator)

    # when
    response = await client.delete(f"/conditions/condition_tree/{child_operator.id}")

    # then
    assert response.status_code == 409
    assert f"Operator with id {child_operator.id} is not a root" in response.text


async def test_assign_tree_to_action__success(client, insert, root_operator, cleanup_db):
    # given
    child_operator = ActionConditionOperator(
        logical_operator=LogicalOperator.OR,
        parent_id=root_operator.id,
        root_id=root_operator.id,
        action_id=root_operator.action_id,
    )
    child_operator = await insert(child_operator)

    action = Action(name="New Action")
    action = await insert(action)

    # when
    response = await client.post(
        f"/conditions/condition_tree/assign?root_id={root_operator.id}&action_id={action.id}"
    )

    # then
    assert response.status_code == 200
    result = response.json()
    assert result == [root_operator.id, action.id]

    async with Session() as db:
        updated_operator = await ActionConditionService.get_condition_operator_by_id(
            root_operator.id, db
        )
        assert updated_operator.action_id == action.id

        updated_child_operator = await ActionConditionService.get_condition_operator_by_id(
            child_operator.id, db
        )
        assert updated_child_operator.action_id == action.id


async def test_assign_tree_to_action__root_not_found(client, insert, cleanup_db):
    # given
    root_id = 999
    action = Action(name="Test Action")
    action = await insert(action)

    # when
    response = await client.post(
        f"/conditions/condition_tree/assign?root_id={root_id}&action_id={action.id}"
    )

    # then
    assert response.status_code == 404
    assert f"Operator with id {root_id} not found" in response.text


async def test_assign_tree_to_action__action_not_found(client, insert, root_operator, cleanup_db):
    # given
    action_id = 999

    # when
    response = await client.post(
        f"/conditions/condition_tree/assign?root_id={root_operator.id}&action_id={action_id}"
    )

    # then
    assert response.status_code == 404
    assert f"Action with id {action_id} not found" in response.text

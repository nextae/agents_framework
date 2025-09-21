from fastapi import APIRouter, Depends

from app.api.dependencies import validate_token
from app.errors.api import ConflictError, NotFoundError
from app.models.action_condition import (
    ActionCondition,
    ActionConditionRequest,
    ActionConditionResponse,
    ActionConditionUpdateRequest,
)
from app.models.action_condition_operator import (
    ActionConditionOperator,
    ActionConditionOperatorRequest,
    ActionConditionOperatorResponse,
    ActionConditionOperatorUpdateRequest,
    NewConditionTreeRequest,
)
from app.services.action_condition_service import ActionConditionService

conditions_router = APIRouter(
    prefix="/conditions", tags=["conditions"], dependencies=[Depends(validate_token)]
)


@conditions_router.post("/condition", status_code=201, response_model=ActionConditionResponse)
async def create_action_condition(condition_request: ActionConditionRequest) -> ActionCondition:
    return await ActionConditionService().create_condition(condition_request)


@conditions_router.post(
    "/operator", status_code=201, response_model=ActionConditionOperatorResponse
)
async def create_action_condition_operator(
    operator_request: ActionConditionOperatorRequest,
) -> ActionConditionOperator:
    return await ActionConditionService().create_condition_operator(operator_request)


@conditions_router.post("/tree", status_code=201, response_model=ActionConditionOperatorResponse)
async def create_new_condition_tree(
    tree_request: NewConditionTreeRequest,
) -> ActionConditionOperator:
    return await ActionConditionService().create_condition_operator_root(tree_request)


@conditions_router.get("/condition", response_model=list[ActionConditionResponse])
async def get_action_conditions() -> list[ActionCondition]:
    return await ActionConditionService().get_conditions()


@conditions_router.get("/operator", response_model=list[ActionConditionOperatorResponse])
async def get_action_condition_operators() -> list[ActionConditionOperator]:
    return await ActionConditionService().get_condition_operators()


@conditions_router.get("/condition/{condition_id}", response_model=ActionConditionResponse)
async def get_action_condition_by_id(condition_id: int) -> ActionCondition:
    condition = await ActionConditionService().get_condition_by_id(condition_id)
    if condition is None:
        raise NotFoundError(f"Action condition with id {condition_id} not found")

    return condition


@conditions_router.get("/operator/{operator_id}", response_model=ActionConditionOperatorResponse)
async def get_action_condition_operator_by_id(operator_id: int) -> ActionConditionOperator:
    operator = await ActionConditionService().get_condition_operator_by_id(operator_id)
    if operator is None:
        raise NotFoundError(f"Action condition operator with id {operator_id} not found")

    return operator


@conditions_router.patch("/condition/{condition_id}", response_model=ActionConditionResponse)
async def update_action_condition_by_id(
    condition_id: int, condition_request: ActionConditionUpdateRequest
) -> ActionCondition:
    return await ActionConditionService().update_condition(condition_id, condition_request)


@conditions_router.patch("/operator/{operator_id}", response_model=ActionConditionOperatorResponse)
async def update_action_condition_operator_by_id(
    operator_id: int, operator_request: ActionConditionOperatorUpdateRequest
) -> ActionConditionOperator:
    return await ActionConditionService().update_condition_operator(operator_id, operator_request)


@conditions_router.delete("/condition/{condition_id}", status_code=204)
async def delete_action_condition_by_id(condition_id: int) -> None:
    await ActionConditionService().delete_condition(condition_id)


@conditions_router.delete("/operator/{operator_id}", status_code=204)
async def delete_action_condition_operator_by_id(operator_id: int) -> None:
    await ActionConditionService().delete_condition_operator(operator_id)


@conditions_router.delete("/condition_tree/{root_id}", status_code=204)
async def delete_tree_by_root_id(root_id: int) -> None:
    operator = await ActionConditionService().get_condition_operator_by_id(root_id)
    if operator is None:
        return None

    if not operator.is_root():
        raise ConflictError(f"Operator with id {root_id} is not a root")

    await ActionConditionService().delete_condition_operator(root_id)


@conditions_router.post("/condition_tree/assign")
async def assign_tree_to_action(root_id: int, action_id: int) -> tuple[int, int]:
    return await ActionConditionService().assign_all_operators_by_root_to_action(root_id, action_id)

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_db, validate_token
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
from app.services.action_condition import ActionConditionService

conditions_router = APIRouter(prefix="/conditions", dependencies=[Depends(validate_token)])


@conditions_router.post("/condition", status_code=201, response_model=ActionConditionResponse)
async def create_action_condition(
    condition_request: ActionConditionRequest, db: AsyncSession = Depends(get_db)
) -> ActionCondition:
    return await ActionConditionService.create_condition(condition_request, db, True)


@conditions_router.post(
    "/operator", status_code=201, response_model=ActionConditionOperatorResponse
)
async def create_action_condition_operator(
    operator_request: ActionConditionOperatorRequest, db: AsyncSession = Depends(get_db)
) -> ActionConditionOperator:
    return await ActionConditionService.create_condition_operator(operator_request, db)


@conditions_router.post("/tree", status_code=201, response_model=ActionConditionOperatorResponse)
async def create_new_condition_tree(
    tree_request: NewConditionTreeRequest, db: AsyncSession = Depends(get_db)
) -> ActionConditionOperator:
    return await ActionConditionService.create_condition_operator_root(tree_request, db)


@conditions_router.get("/condition", response_model=list[ActionConditionResponse])
async def get_action_conditions(
    db: AsyncSession = Depends(get_db),
) -> list[ActionCondition]:
    return await ActionConditionService.get_conditions(db)


@conditions_router.get("/operator", response_model=list[ActionConditionOperatorResponse])
async def get_action_condition_operators(
    db: AsyncSession = Depends(get_db),
) -> list[ActionConditionOperator]:
    return await ActionConditionService.get_condition_operators(db)


@conditions_router.get("/condition/{condition_id}", response_model=ActionConditionResponse)
async def get_action_condition_by_id(
    condition_id: int, db: AsyncSession = Depends(get_db)
) -> ActionCondition:
    condition = await ActionConditionService.get_condition_by_id(condition_id, db)
    if condition is None:
        raise NotFoundError(f"Action condition with id {condition_id} not found")

    return condition


@conditions_router.get("/operator/{operator_id}", response_model=ActionConditionOperatorResponse)
async def get_action_condition_operator_by_id(
    operator_id: int, db: AsyncSession = Depends(get_db)
) -> ActionConditionOperator:
    operator = await ActionConditionService.get_condition_operator_by_id(operator_id, db)
    if operator is None:
        raise NotFoundError(f"Action condition operator with id {operator_id} not found")

    return operator


@conditions_router.patch("/condition/{condition_id}", response_model=ActionConditionResponse)
async def update_action_condition_by_id(
    condition_id: int,
    condition_request: ActionConditionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ActionCondition:
    return await ActionConditionService.update_condition(condition_id, condition_request, db)


@conditions_router.patch("/operator/{operator_id}", response_model=ActionConditionOperatorResponse)
async def update_action_condition_operator_by_id(
    operator_id: int,
    operator_request: ActionConditionOperatorUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ActionConditionOperator:
    return await ActionConditionService.update_condition_operator(operator_id, operator_request, db)


@conditions_router.delete("/condition/{condition_id}", status_code=204)
async def delete_action_condition_by_id(
    condition_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await ActionConditionService.delete_condition(condition_id, db)


@conditions_router.delete("/operator/{operator_id}", status_code=204)
async def delete_action_condition_operator_by_id(
    operator_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await ActionConditionService.delete_condition_operator(operator_id, db)


@conditions_router.delete("/condition_tree/{root_id}", status_code=204)
async def delete_tree_by_root_id(root_id: int, db: AsyncSession = Depends(get_db)) -> None:
    operator = await ActionConditionService.get_condition_operator_by_id(root_id, db)
    if operator is None:
        return None

    if not operator.is_root():
        raise ConflictError(f"Operator with id {root_id} is not a root")

    await ActionConditionService.delete_condition_operator(root_id, db, True)


@conditions_router.post("/condition_tree/assign")
async def assign_tree_to_action(
    root_id: int, action_id: int, db: AsyncSession = Depends(get_db)
) -> tuple[int, int]:
    return await ActionConditionService.assign_all_operators_by_root_to_action(
        root_id, action_id, db
    )

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.errors import NotFoundError
from app.db.database import get_db
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
)
from app.services.action_condition import ActionConditionService

condition_router = APIRouter(prefix="/conditions")


@condition_router.post("/condition", status_code=201)
async def create_action_condition(
    condition_request: ActionConditionRequest, db: AsyncSession = Depends(get_db)
):
    condition = await ActionConditionService.create_condition(condition_request, db)

    return ActionConditionResponse.model_validate(condition)


@condition_router.post("/operator", status_code=201)
async def create_action_condition_operator(
    operator_request: ActionConditionOperatorRequest, db: AsyncSession = Depends(get_db)
):
    operator = await ActionConditionService.create_condition_operator(
        operator_request, db
    )

    return ActionConditionOperatorResponse.model_validate(operator)


@condition_router.post("/tree")
async def create_new_condition_tree(
    operator_request: ActionConditionOperatorRequest, db: AsyncSession = Depends(get_db)
):
    operator = await ActionConditionService.create_condition_operator_root(
        operator_request, db
    )

    return ActionConditionOperatorResponse.model_validate(operator)


@condition_router.get("/condition", response_model=list[ActionConditionResponse])
async def get_action_conditions(
    db: AsyncSession = Depends(get_db),
) -> list[ActionCondition]:
    return await ActionConditionService.get_conditions(db)


@condition_router.get("/operator", response_model=list[ActionConditionOperatorResponse])
async def get_action_condition_operators(
    db: AsyncSession = Depends(get_db),
) -> list[ActionConditionOperator]:
    return await ActionConditionService.get_condition_operators(db)


@condition_router.get(
    "/condition/{condition_id}", response_model=ActionConditionResponse
)
async def get_action_condition_by_id(
    condition_id: int, db: AsyncSession = Depends(get_db)
) -> ActionCondition:
    condition = await ActionConditionService.get_condition_by_id(condition_id, db)
    if condition is None:
        raise NotFoundError(f"Action condition with id {condition_id} not found")

    return condition


@condition_router.get(
    "/operator/{operator_id}", response_model=ActionConditionOperatorResponse
)
async def get_action_condition_operator_by_id(
    operator_id: int, db: AsyncSession = Depends(get_db)
) -> ActionConditionOperator:
    operator = await ActionConditionService.get_condition_operator_by_id(
        operator_id, db
    )
    if operator is None:
        raise NotFoundError(
            f"Action condition operator with id {operator_id} not found"
        )

    return operator


@condition_router.put(
    "/condition/{condition_id}", response_model=ActionConditionResponse
)
async def update_action_condition_by_id(
    condition_id: int,
    condition_request: ActionConditionUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ActionConditionService.update_condition(
        condition_id, condition_request, db
    )


@condition_router.put(
    "/operator/{operator_id}", response_model=ActionConditionOperatorResponse
)
async def update_action_condition_operator_by_id(
    operator_id: int,
    operator_request: ActionConditionOperatorUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await ActionConditionService.update_condition_operator(
        operator_id, operator_request, db
    )


@condition_router.delete(
    "/condition/{condition_id}", response_model=ActionConditionResponse
)
async def delete_action_condition_by_id(
    condition_id: int, db: AsyncSession = Depends(get_db)
):
    return await ActionConditionService.delete_condition(condition_id, db)


@condition_router.delete(
    "/operator/{operator_id}", response_model=ActionConditionOperatorResponse
)
async def delete_action_condition_operator_by_id(
    operator_id: int, db: AsyncSession = Depends(get_db)
):
    return await ActionConditionService.delete_condition_operator(operator_id, db)


@condition_router.delete("/condition_tree/{root_id}")
async def delete_tree_by_root_id(root_id: int, db: AsyncSession = Depends(get_db)):
    operator = await ActionConditionService.get_condition_operator_by_id(root_id, db)
    if not operator.is_root():
        raise ValueError("Given id is not a root")
    return await ActionConditionService.delete_condition_operator(root_id, db, True)

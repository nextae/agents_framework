from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_db, validate_token
from app.errors.api import ConflictError, NotFoundError
from app.errors.conditions import ConditionEvaluationError
from app.models.action import (
    Action,
    ActionEvaluationResult,
    ActionRequest,
    ActionResponse,
    ActionUpdateRequest,
)
from app.services.action import ActionService

actions_router = APIRouter(prefix="/actions", dependencies=[Depends(validate_token)])


@actions_router.post("", status_code=201, response_model=ActionResponse)
async def create_action(action: ActionRequest, db: AsyncSession = Depends(get_db)) -> Action:
    return await ActionService.create_action(action, db)


@actions_router.get("", response_model=list[ActionResponse])
async def get_actions(db: AsyncSession = Depends(get_db)) -> list[Action]:
    return await ActionService.get_actions(db)


@actions_router.get("/{action_id}", response_model=ActionResponse)
async def get_action_by_id(action_id: int, db: AsyncSession = Depends(get_db)) -> Action:
    action = await ActionService.get_action_by_id(action_id, db)
    if action is None:
        raise NotFoundError(f"Action with id {action_id} not found")

    return action


@actions_router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: int,
    action_update: ActionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> Action:
    return await ActionService.update_action(action_id, action_update, db)


@actions_router.delete("/{action_id}", status_code=204)
async def delete_action(action_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await ActionService.delete_action(action_id, db)


@actions_router.post("/{action_id}/evaluate_conditions")
async def evaluate_action_conditions(
    action_id: int, db: AsyncSession = Depends(get_db)
) -> ActionEvaluationResult:
    try:
        return await ActionService.evaluate_action_conditions(action_id, db)
    except ConditionEvaluationError as e:
        raise ConflictError(str(e))

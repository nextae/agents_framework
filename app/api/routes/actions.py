from fastapi import APIRouter, Depends

from app.api.dependencies import validate_token
from app.errors.api import NotFoundError
from app.models.action import (
    Action,
    ActionEvaluationResult,
    ActionRequest,
    ActionResponse,
    ActionUpdateRequest,
)
from app.services.action_condition_service import ActionConditionService
from app.services.action_service import ActionService

actions_router = APIRouter(
    prefix="/actions", tags=["actions"], dependencies=[Depends(validate_token)]
)


@actions_router.post("", status_code=201, response_model=ActionResponse)
async def create_action(action: ActionRequest) -> Action:
    return await ActionService().create_action(action)


@actions_router.get("", response_model=list[ActionResponse])
async def get_actions() -> list[Action]:
    return await ActionService().get_actions()


@actions_router.get("/{action_id}", response_model=ActionResponse)
async def get_action_by_id(action_id: int) -> Action:
    action = await ActionService().get_action_by_id(action_id)
    if action is None:
        raise NotFoundError(f"Action with id {action_id} not found")

    return action


@actions_router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(action_id: int, action_update: ActionUpdateRequest) -> Action:
    return await ActionService().update_action(action_id, action_update)


@actions_router.delete("/{action_id}", status_code=204)
async def delete_action(action_id: int) -> None:
    await ActionService().delete_action(action_id)


@actions_router.post("/{action_id}/evaluate_conditions")
async def evaluate_action_conditions(action_id: int) -> ActionEvaluationResult:
    return await ActionConditionService().evaluate_action_conditions(action_id)

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_db
from app.models.action import Action
from app.models.action_param import ActionParam
from app.services.action import ActionService

actions_router = APIRouter(prefix="/actions")


@actions_router.post("/", response_model=Action)
async def create_action(action: Action, db: AsyncSession = Depends(get_db)) -> Action:
    return await ActionService.create_action(action, db)


@actions_router.post("/with_params", response_model=tuple[Action, list[ActionParam]])
async def create_action_with_params(
    action: Action, params: list[ActionParam], db: AsyncSession = Depends(get_db)
) -> tuple[Action, list[ActionParam]]:
    action = await ActionService.create_action_with_params(action, params, db)
    return await get_action_by_id(action.id, db)


@actions_router.get("/", response_model=list[tuple[Action, list[ActionParam]]] | None)
async def get_actions(
    db: AsyncSession = Depends(get_db),
) -> list[tuple[Action, list[ActionParam]]] | None:
    actions = await ActionService.get_actions(db)
    result = []
    for action in actions:
        result.append((action, action.params))
    return result


@actions_router.get(
    "/{action_id}", response_model=tuple[Action, list[ActionParam]] | None
)
async def get_action_by_id(
    action_id: int, db: AsyncSession = Depends(get_db)
) -> tuple[Action, list[ActionParam]] | None:
    action = await ActionService.get_action_by_id(action_id, db)
    if action is None:
        return None
    return action, action.params


@actions_router.put("/{action_id}", response_model=Action | None)
async def update_action(
    action_id: int, action: Action, db: AsyncSession = Depends(get_db)
) -> Action | None:
    return await ActionService.update_action(action_id, action, db)


@actions_router.delete("/{action_id}", response_model=int | None)
async def delete_action(
    action_id: int, db: AsyncSession = Depends(get_db)
) -> int | None:
    return await ActionService.delete_action(action_id, db)

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.dependencies import get_db, validate_token
from app.errors.api import NotFoundError
from app.models.action_param import (
    ActionParam,
    ActionParamRequest,
    ActionParamResponse,
    ActionParamUpdateRequest,
)
from app.services.action_param import ActionParamService

params_router = APIRouter(prefix="/params", dependencies=[Depends(validate_token)])


@params_router.post("", status_code=201, response_model=ActionParamResponse)
async def create_param(
    param: ActionParamRequest, db: AsyncSession = Depends(get_db)
) -> ActionParam:
    return await ActionParamService.create_action_param(param, db)


@params_router.get("/{action_param_id}", response_model=ActionParamResponse)
async def get_action_param_by_id(
    action_param_id: int, db: AsyncSession = Depends(get_db)
) -> ActionParam:
    param = await ActionParamService.get_action_param_by_id(action_param_id, db)
    if param is None:
        raise NotFoundError(f"ActionParam with id {action_param_id} not found")

    return param


@params_router.put("/{action_param_id}", response_model=ActionParamResponse)
async def update_action_param(
    action_param_id: int,
    action_param_update: ActionParamUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ActionParam:
    return await ActionParamService.update_action_param(
        action_param_id, action_param_update, db
    )


@params_router.delete("/{action_param_id}", status_code=204)
async def delete_action_param(
    action_param_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    return await ActionParamService.delete_action_param(action_param_id, db)

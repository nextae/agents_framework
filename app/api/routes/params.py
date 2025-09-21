from fastapi import APIRouter, Depends

from app.api.dependencies import validate_token
from app.errors.api import NotFoundError
from app.models.action_param import (
    ActionParam,
    ActionParamRequest,
    ActionParamResponse,
    ActionParamUpdateRequest,
)
from app.services.action_param_service import ActionParamService

params_router = APIRouter(prefix="/params", tags=["params"], dependencies=[Depends(validate_token)])


@params_router.post("", status_code=201, response_model=ActionParamResponse)
async def create_param(param: ActionParamRequest) -> ActionParam:
    return await ActionParamService().create_action_param(param)


@params_router.get("/{action_param_id}", response_model=ActionParamResponse)
async def get_action_param_by_id(action_param_id: int) -> ActionParam:
    param = await ActionParamService().get_action_param_by_id(action_param_id)
    if param is None:
        raise NotFoundError(f"ActionParam with id {action_param_id} not found")

    return param


@params_router.patch("/{action_param_id}", response_model=ActionParamResponse)
async def update_action_param(
    action_param_id: int, action_param_update: ActionParamUpdateRequest
) -> ActionParam:
    return await ActionParamService().update_action_param(action_param_id, action_param_update)


@params_router.delete("/{action_param_id}", status_code=204)
async def delete_action_param(action_param_id: int) -> None:
    await ActionParamService().delete_action_param(action_param_id)

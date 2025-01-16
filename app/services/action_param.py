from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.action import ActionService
from app.api.errors import NotFoundError
from app.models.action_param import (
    ActionParam,
    ActionParamRequest,
    ActionParamUpdateRequest,
)


class ActionParamService:
    @staticmethod
    async def create_action_param(
        action_param_request: ActionParamRequest, db: AsyncSession
    ) -> ActionParam:
        param = ActionParam.model_validate(action_param_request)

        action = await ActionService.get_action_by_id(param.action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {param.action_id} not found")

        db.add(param)
        await db.commit()
        await db.refresh(param)
        return param

    @staticmethod
    async def get_action_params(action_id: int, db: AsyncSession) -> list[ActionParam]:
        result = await db.exec(
            select(ActionParam).where(ActionParam.action_id == action_id)
        )
        return list(result.all())

    @staticmethod
    async def get_action_param_by_id(
        action_param_id: int, db: AsyncSession
    ) -> ActionParam | None:
        return await db.get(ActionParam, action_param_id)

    @staticmethod
    async def update_action_param(
        action_param_id: int,
        action_param_update: ActionParamUpdateRequest,
        db: AsyncSession,
    ) -> ActionParam:
        param = await ActionParamService.get_action_param_by_id(action_param_id, db)
        if not param:
            raise NotFoundError(f"ActionParam with id {action_param_id} not found")

        action = await ActionService.get_action_by_id(param.action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {param.action_id} not found")

        param_update_data = action_param_update.model_dump(exclude_unset=True)
        param.sqlmodel_update(param_update_data)

        db.add(param)
        await db.commit()
        await db.refresh(param)
        return param

    @staticmethod
    async def delete_action_param(action_param_id: int, db: AsyncSession) -> None:
        param = await ActionParamService.get_action_param_by_id(action_param_id, db)
        if not param:
            raise NotFoundError(f"ActionParam with id {action_param_id} not found")

        await db.delete(param)
        await db.commit()

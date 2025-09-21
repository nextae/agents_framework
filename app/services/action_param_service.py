from app.errors.api import NotFoundError
from app.models.action_param import (
    ActionParam,
    ActionParamRequest,
    ActionParamUpdateRequest,
)

from .action_service import ActionService
from .base_service import BaseService


class ActionParamService(BaseService):
    async def create_action_param(self, action_param_request: ActionParamRequest) -> ActionParam:
        """
        Create a new action parameter.

        Args:
            action_param_request (ActionParamRequest): The request to create the parameter.

        Returns:
            ActionParam: The created action parameter.
        """

        param = ActionParam.model_validate(action_param_request)

        async with self.unit_of_work as uow:
            action = await ActionService(uow).get_action_by_id(param.action_id)
            if action is None:
                raise NotFoundError(f"Action with id {param.action_id} not found")

            return await uow.params.create(param)

    async def get_action_param_by_id(self, action_param_id: int) -> ActionParam | None:
        """
        Get an action parameter by its ID.

        Args:
            action_param_id (int): The parameter ID.

        Returns:
            ActionParam | None: The parameter, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.params.find_by_id(action_param_id)

    async def update_action_param(
        self, action_param_id: int, action_param_update: ActionParamUpdateRequest
    ) -> ActionParam:
        """
        Update an existing action parameter.

        Args:
            action_param_id (int): The parameter ID.
            action_param_update (ActionParamUpdateRequest): The update request.

        Returns:
            ActionParam: The updated parameter.
        """

        async with self.unit_of_work as uow:
            param = await self.get_action_param_by_id(action_param_id)
            if param is None:
                raise NotFoundError(f"ActionParam with id {action_param_id} not found")

            if action_param_update.action_id is not None:
                action = await ActionService(uow).get_action_by_id(action_param_update.action_id)
                if action is None:
                    raise NotFoundError(f"Action with id {action_param_update.action_id} not found")

            param_update_data = action_param_update.model_dump(exclude_unset=True)
            param.sqlmodel_update(param_update_data)

            return await uow.params.update(param)

    async def delete_action_param(self, action_param_id: int) -> None:
        """
        Delete an action parameter by its ID.

        Args:
            action_param_id (int): The parameter ID.
        """

        async with self.unit_of_work as uow:
            await uow.params.delete_by_id(action_param_id)

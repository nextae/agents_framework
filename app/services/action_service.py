from sqlalchemy.exc import IntegrityError

from app.errors.api import ConflictError, NotFoundError
from app.models.action import (
    Action,
    ActionRequest,
    ActionUpdateRequest,
)

from .base_service import BaseService


class ActionService(BaseService):
    async def create_action(self, action_request: ActionRequest) -> Action:
        """
        Create a new action.

        Args:
            action_request (ActionRequest): The request to create the new action.

        Returns:
            Action: The created action.
        """

        action = Action.model_validate(action_request)

        async with self.unit_of_work as uow:
            if action_request.triggered_agent_id is not None:
                from app.services.agent_service import AgentService

                triggered_agent = await AgentService(uow).get_agent_by_id(
                    action_request.triggered_agent_id
                )
                if triggered_agent is None:
                    raise NotFoundError(
                        f"Agent with id {action_request.triggered_agent_id} not found"
                    )

            try:
                return await uow.actions.create(action)
            except IntegrityError:
                raise ConflictError(f"Action with name {action.name} already exists")

    async def get_actions(self) -> list[Action]:
        """
        Get all actions.

        Returns:
            list[Action]: A list of all actions.
        """

        async with self.unit_of_work as uow:
            return await uow.actions.find_all()

    async def get_action_by_id(self, action_id: int) -> Action | None:
        """
        Get an action by its ID.

        Args:
            action_id (int): The ID of the action to retrieve.

        Returns:
            Action | None: The action with the specified ID, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.actions.find_by_id(action_id)

    async def update_action(self, action_id: int, action_update: ActionUpdateRequest) -> Action:
        """
        Update an existing action.

        Args:
            action_id (int): The ID of the action to update.
            action_update (ActionUpdateRequest): The request to update the action.

        Returns:
            Action: The updated action.
        """

        async with self.unit_of_work as uow:
            action = await self.get_action_by_id(action_id)
            if not action:
                raise NotFoundError(f"Action with id {action_id} not found")

            action_update_data = action_update.model_dump(exclude_unset=True)

            if action_update.triggered_agent_id is not None:
                from app.services.agent_service import AgentService

                triggered_agent = await AgentService(uow).get_agent_by_id(
                    action_update.triggered_agent_id
                )
                if triggered_agent is None:
                    raise NotFoundError(
                        f"Agent with id {action_update.triggered_agent_id} not found"
                    )

            action.sqlmodel_update(action_update_data)

            try:
                return await uow.actions.update(action)
            except IntegrityError:
                raise ConflictError(f"Action with name {action_update.name} already exists")

    async def delete_action(self, action_id: int) -> None:
        """
        Delete an action by its ID.

        Args:
            action_id (int): The ID of the action to delete.
        """

        async with self.unit_of_work as uow:
            from app.services.action_condition_service import ActionConditionService

            action = await self.get_action_by_id(action_id)
            if not action:
                return None

            condition_service = ActionConditionService(uow)

            root_operator = await condition_service.get_root_operator_for_action_id(action_id)
            if root_operator is not None:
                await condition_service.delete_condition_operator(root_operator.id)

            await uow.actions.delete(action)

    async def agent_has_trigger_actions(self, agent_id: int) -> bool:
        """
        Check if an agent has any trigger actions.

        Args:
            agent_id (int): The ID of the agent.

        Returns:
            bool: True if the agent has trigger actions, False otherwise.
        """

        async with self.unit_of_work as uow:
            action = await uow.actions.find_first_by_triggered_agent_id(agent_id)
            return action is not None

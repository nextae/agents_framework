from app.errors.api import ConflictError, NotFoundError
from app.errors.conditions import ConditionEvaluationError
from app.models.action import Action, ActionEvaluationResult
from app.models.action_condition import (
    ActionCondition,
    ActionConditionRequest,
    ActionConditionUpdateRequest,
)
from app.models.action_condition_operator import (
    ActionConditionOperator,
    ActionConditionOperatorRequest,
    ActionConditionOperatorUpdateRequest,
    NewConditionTreeRequest,
)
from app.models.action_condition_tree import ActionConditionTree, ActionConditionTreeNode

from .agent_service import AgentService
from .base_service import BaseService
from .global_state_service import GlobalStateService


class ActionConditionService(BaseService):
    async def get_root_operator_for_action_id(
        self, action_id: int
    ) -> ActionConditionOperator | None:
        """
        Get the root operator for a given action ID.

        Args:
            action_id (int): The ID of the action.

        Returns:
            ActionConditionOperator | None: The root operator, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.operators.find_root_by_action_id(action_id)

    async def get_condition_tree(self, action_id: int) -> ActionConditionTree | None:
        """
        Get the condition tree for a given action ID.

        Args:
            action_id (int): The action ID.

        Returns:
            ActionConditionTree | None: The condition tree, or None if not found.
        """

        async with self.unit_of_work as uow:
            root = await self.get_root_operator_for_action_id(action_id)
            if root is None:
                return None

            conditions = await uow.conditions.find_all_by_root_id(root.id)
            operators = await uow.operators.find_all_by_root_id(root.id)

            global_state = await GlobalStateService(uow).get_state()

            agent_ids = [
                condition.state_agent_id
                for condition in conditions
                if condition.state_agent_id is not None
            ]
            agents = await uow.agents.find_all_by_ids(agent_ids)

            empty_root_node = ActionConditionTreeNode.from_operator(root)
            root_node = ActionConditionTreeNode.build(empty_root_node, conditions, operators)
            return ActionConditionTree(root_node, global_state, agents)

    async def create_condition_operator(
        self, operator_request: ActionConditionOperatorRequest
    ) -> ActionConditionOperator:
        """
        Create a new condition operator.

        Args:
            operator_request (ActionConditionOperatorRequest): The request to create the operator.

        Returns:
            ActionConditionOperator: The created operator.
        """

        condition_operator = ActionConditionOperator.model_validate(operator_request)

        async with self.unit_of_work as uow:
            await self._validate_operator_ids(condition_operator)
            return await uow.operators.create(condition_operator)

    async def _validate_operator_ids(
        self, operator: ActionConditionOperator | ActionConditionOperatorUpdateRequest
    ) -> None:
        """
        Validate the IDs of the given operator.

        Args:
            operator (ActionConditionOperator | ActionConditionOperatorUpdateRequest):
                The operator to validate.

        Raises:
            NotFoundError: If the action, parent, or root operator does not exist.
            ConflictError: If the root operator is not a root.
        """

        async with self.unit_of_work as uow:
            await self._validate_parent_and_root(operator.parent_id, operator.root_id)

            if operator.action_id is not None:
                action = await uow.actions.find_by_id(operator.action_id)
                if action is None:
                    raise NotFoundError(f"Action with id {operator.action_id} not found")

    async def create_condition_operator_root(
        self, tree_request: NewConditionTreeRequest
    ) -> ActionConditionOperator:
        """
        Create a new root condition operator.

        Args:
            tree_request (NewConditionTreeRequest): The request to create the root operator.

        Returns:
            ActionConditionOperator: The created root operator.
        """

        operator = ActionConditionOperator.model_validate(tree_request)

        async with self.unit_of_work as uow:
            action = await uow.actions.find_by_id(operator.action_id)
            if action is None:
                raise NotFoundError(f"Action with id {operator.action_id} not found")

            root = await self.get_root_operator_for_action_id(operator.action_id)
            if root is not None:
                raise ConflictError(
                    f"Action with id {operator.action_id} already has root assigned with id {root.id}"  # noqa: E501
                )

            operator = await uow.operators.create(operator)
            operator.root_id = operator.id
            return await uow.operators.update(operator)

    async def create_condition(self, condition_request: ActionConditionRequest) -> ActionCondition:
        """
        Create a new condition.

        Args:
            condition_request (ActionConditionRequest): The request to create the condition.

        Returns:
            ActionCondition: The created condition.
        """

        condition = ActionCondition.model_validate(condition_request)

        async with self.unit_of_work as uow:
            await self._validate_condition_ids(condition)
            await self._validate_condition_logic(condition)
            return await uow.conditions.create(condition)

    async def _validate_condition_ids(
        self, condition: ActionCondition | ActionConditionUpdateRequest
    ) -> None:
        """
        Validate the IDs of the given condition.

        Args:
            condition (ActionCondition | ActionConditionUpdateRequest): The condition to validate.

        Raises:
            NotFoundError: If the state agent, parent or root operator does not exist.
            ConflictError: If the root operator is not a root.
        """

        async with self.unit_of_work as uow:
            await self._validate_parent_and_root(condition.parent_id, condition.root_id)

            if condition.state_agent_id is not None:
                agent = await AgentService(uow).get_agent_by_id(condition.state_agent_id)
                if agent is None:
                    raise NotFoundError(f"Agent with id {condition.state_agent_id} not found")

    async def _validate_condition_logic(self, condition: ActionCondition) -> None:
        """
        Validate the logic of the given condition.

        Args:
            condition (ActionCondition): The condition to validate.

        Raises:
            ConflictError: If the condition logic is invalid.
        """

        async with self.unit_of_work as uow:
            global_state = await GlobalStateService(uow).get_state()
            agent_state = {}
            if condition.state_agent_id is not None:
                agent = await AgentService(uow).get_agent_by_id(condition.state_agent_id)
                agent_state = {agent.id: agent.combined_state}

            try:
                ActionConditionTreeNode.from_condition(condition).evaluate(
                    global_state.state, agent_state
                )
            except ConditionEvaluationError as e:
                raise ConflictError(str(e)) from e

    async def get_condition_operator_by_id(
        self, operator_id: int
    ) -> ActionConditionOperator | None:
        """
        Get a condition operator by its ID.

        Args:
            operator_id (int): The operator ID.

        Returns:
            ActionConditionOperator | None: The operator, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.operators.find_by_id(operator_id)

    async def get_condition_by_id(self, condition_id: int) -> ActionCondition | None:
        """
        Get a condition by its ID.

        Args:
            condition_id (int): The condition ID.

        Returns:
            ActionCondition | None: The condition, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.conditions.find_by_id(condition_id)

    async def get_conditions(self) -> list[ActionCondition]:
        """
        Get all conditions.

        Returns:
            list[ActionCondition]: List of all conditions.
        """

        async with self.unit_of_work as uow:
            return await uow.conditions.find_all()

    async def get_condition_operators(self) -> list[ActionConditionOperator]:
        """
        Get all condition operators.

        Returns:
            list[ActionConditionOperator]: List of all operators.
        """

        async with self.unit_of_work as uow:
            return await uow.operators.find_all()

    async def assign_all_operators_by_root_to_action(
        self, root_id: int, action_id: int
    ) -> tuple[int, int]:
        """
        Assign all operators by root to an action.

        Args:
            root_id (int): The root operator ID.
            action_id (int): The action ID.

        Returns:
            tuple[int, int]: The root ID and action ID.
        """

        async with self.unit_of_work as uow:
            operator = await self.get_condition_operator_by_id(root_id)
            if operator is None:
                raise NotFoundError(f"Operator with id {root_id} not found")

            if not operator.is_root():
                raise ConflictError(f"Operator with id {root_id} is not a root")

            action = await uow.actions.find_by_id(action_id)
            if action is None:
                raise NotFoundError(f"Action with id {action_id} not found")

            operators = await uow.operators.find_all_by_root_id(root_id)
            for operator in operators:
                operator.action_id = action.id
                await uow.operators.update(operator)

            return root_id, action_id

    async def update_condition(
        self, condition_id: int, condition_update: ActionConditionUpdateRequest
    ) -> ActionCondition:
        """
        Update an existing condition.

        Args:
            condition_id (int): The condition ID.
            condition_update (ActionConditionUpdateRequest): The update request.

        Returns:
            ActionCondition: The updated condition.
        """

        async with self.unit_of_work as uow:
            condition = await self.get_condition_by_id(condition_id)
            if not condition:
                raise NotFoundError(f"Condition with id {condition_id} not found")

            await self._validate_condition_ids(condition_update)

            condition_update_data = condition_update.model_dump(exclude_unset=True)
            condition.sqlmodel_update(condition_update_data)

            await self._validate_condition_logic(condition)
            return await uow.conditions.update(condition)

    async def update_condition_operator(
        self, operator_id: int, operator_update: ActionConditionOperatorUpdateRequest
    ) -> ActionConditionOperator:
        """
        Update an existing condition operator.

        Args:
            operator_id (int): The operator ID.
            operator_update (ActionConditionOperatorUpdateRequest): The update request.

        Returns:
            ActionConditionOperator: The updated operator.
        """

        async with self.unit_of_work as uow:
            operator = await self.get_condition_operator_by_id(operator_id)
            if not operator:
                raise NotFoundError(f"Operator with id {operator_id} not found")

            await self._validate_operator_ids(operator_update)

            operator_update_data = operator_update.model_dump(exclude_unset=True)
            operator.sqlmodel_update(operator_update_data)

            return await uow.operators.update(operator)

    async def delete_condition_operator(self, operator_id: int) -> None:
        """
        Delete a condition operator by its ID. This cascades to delete all children.

        Args:
            operator_id (int): The operator ID.
        """

        async with self.unit_of_work as uow:
            await uow.operators.delete_by_id(operator_id)

    async def delete_condition(self, condition_id: int) -> None:
        """
        Delete a condition by its ID.

        Args:
            condition_id (int): The condition ID.
        """

        async with self.unit_of_work as uow:
            await uow.conditions.delete_by_id(condition_id)

    async def evaluate_action_conditions(self, action_id: int) -> ActionEvaluationResult:
        """
        Evaluate the conditions for an action.

        Args:
            action_id (int): The ID of the action to evaluate.

        Returns:
            ActionEvaluationResult: The result of the condition evaluation.
        """

        async with self.unit_of_work as uow:
            action = await uow.actions.find_by_id(action_id)
            if action is None:
                raise NotFoundError(f"Action with id {action_id} not found")

            try:
                result = await self.evaluate_conditions(action)
            except ConditionEvaluationError as e:
                raise ConflictError(str(e))

            return ActionEvaluationResult(action_id=action_id, result=result)

    async def evaluate_conditions(self, action: Action) -> bool:
        """
        Evaluate the conditions for an action.

        Args:
            action (Action): The action to evaluate.

        Returns:
            bool: The result of the condition evaluation.
        """

        tree = await self.get_condition_tree(action.id)
        return tree.evaluate() if tree else True

    async def _validate_parent_and_root(self, parent_id: int | None, root_id: int | None) -> None:
        """
        Validate parent and root operator IDs.

        Args:
            parent_id (int | None): The parent operator ID.
            root_id (int | None): The root operator ID.

        Raises:
            NotFoundError: If parent or root not found.
            ConflictError: If root is not a root operator.
        """

        if parent_id is not None:
            parent = await self.get_condition_operator_by_id(parent_id)
            if parent is None:
                raise NotFoundError(f"Operator with id {parent_id} not found")

        if root_id is not None:
            root = await self.get_condition_operator_by_id(root_id)
            if root is None:
                raise NotFoundError(f"Root with id {root_id} not found")

            if not root.is_root():
                raise ConflictError(f"Operator with id {root_id} is not a root")

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.errors import NotFoundError
from app.models.action_condition import (
    ActionCondition,
    ActionConditionRequest,
    ActionConditionUpdateRequest,
    ComparisonMethod,
)
from app.models.action_condition_operator import (
    ActionConditionOperator,
    ActionConditionOperatorRequest,
    ActionConditionOperatorUpdateRequest,
    LogicalOperator,
)
from app.models.global_state import StateValue
from app.services.global_state import GlobalStateService


class ActionConditionTreeNode:
    def __init__(
        self,
        node_id: int,
        logical_operator: LogicalOperator | None,
        comparison: ComparisonMethod | None,
        state_variable_name: str | None,
        expected_value: str | None,
    ):
        self.node_id: int = node_id
        self.logical_operator: LogicalOperator | None = logical_operator
        self.comparison: ComparisonMethod | None = comparison
        self.state_variable_name: str | None = state_variable_name
        self.expected_value: str | None = expected_value
        self.children: list[ActionConditionTreeNode] = []
        self.parent: ActionConditionTreeNode = self
        self.root: ActionConditionTreeNode = self

    def add_child(self, child: "ActionConditionTreeNode"):
        self.children.append(child)
        child.parent = self
        child.root = self.root

    async def evaluate_tree(self, db: AsyncSession) -> bool:
        return await self.root.__evaluate(db)

    async def __evaluate(self, db: AsyncSession) -> bool:
        if len(self.children) == 0:
            state_var = await self.__get_state_variable(db)

            if state_var is None:
                raise KeyError(f"No state variable {self.state_variable_name} found")

            if self.comparison in {
                ComparisonMethod.GREATER,
                ComparisonMethod.LESS,
                ComparisonMethod.AT_LEAST,
                ComparisonMethod.AT_MOST,
            }:
                try:
                    state_var = float(state_var)
                    expected_value = float(self.expected_value)
                except ValueError:
                    raise TypeError(
                        f"Comparison '{self.comparison.name}' is not valid for non-numeric values: "  # noqa: E501
                        f"state_var={state_var}, expected_value={self.expected_value}"
                    )
            else:
                expected_value = self.expected_value

            if self.comparison == ComparisonMethod.EQUAL:
                return state_var == expected_value
            elif self.comparison == ComparisonMethod.NOT_EQUAL:
                return state_var != expected_value
            elif self.comparison == ComparisonMethod.GREATER:
                return state_var > expected_value
            elif self.comparison == ComparisonMethod.LESS:
                return state_var < expected_value
            elif self.comparison == ComparisonMethod.AT_LEAST:
                return state_var >= expected_value
            elif self.comparison == ComparisonMethod.AT_MOST:
                return state_var <= expected_value
        else:
            results = [await child.__evaluate(db) for child in self.children]
            if self.logical_operator == LogicalOperator.AND:
                return all(results)
            return any(results)

    async def validate_leaf(self, db: AsyncSession) -> bool:
        if self.logical_operator is not None:
            raise ValueError("Node must be a leaf to validate")
        try:
            await self.__evaluate(db)
        except (KeyError, TypeError, ValueError):
            return False
        return True

    async def __get_state_variable(self, db: AsyncSession) -> StateValue | None:
        from app.services.agent import AgentService

        if self.state_variable_name.startswith("global"):
            state = (await GlobalStateService.get_state(db)).state
        elif self.state_variable_name.startswith("agent-"):
            agent_id = int(self.state_variable_name.split("/")[0].split("-")[1])
            agent = await AgentService.get_agent_by_id(agent_id, db)
            state = agent.state
        else:
            raise ValueError(
                f"State variable name '{self.state_variable_name}' is not valid"
            )

        keys = self.state_variable_name.split("/")[1:]
        current = state

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
                else:
                    return None  # Unsupported type
            return current
        except (KeyError, IndexError, ValueError, TypeError):
            return None


class ActionConditionService:
    @staticmethod
    async def get_all_conditions_by_root_id(
        root_id: int, db: AsyncSession
    ) -> list[ActionCondition | ActionConditionOperator]:
        conditions = await db.exec(
            select(ActionCondition).where(ActionCondition.root_id == root_id)
        )
        conditions = list(conditions.all())

        operators = await db.exec(
            select(ActionConditionOperator).where(
                ActionConditionOperator.root_id == root_id
            )
        )
        operators = list(operators.all())
        return conditions + operators

    @staticmethod
    async def get_all_conditions_by_action_id(
        action_id: int, db: AsyncSession
    ) -> list[ActionCondition | ActionConditionOperator]:
        operators = await db.exec(
            select(ActionConditionOperator).where(
                ActionConditionOperator.action_id == action_id
            )
        )
        operators = list(operators.all())

        root = [op for op in operators if op.is_root()]
        if len(root) == 0:
            raise NotFoundError(
                f"No root node found in the input for action_id: {action_id}"
            )
        if len(root) > 1:
            raise ValueError(f"Found multiple roots for action_id: {action_id}")
        root = root[0]

        conditions = await db.exec(
            select(ActionCondition).where(ActionCondition.root_id == root.id)
        )
        conditions = list(conditions.all())
        return conditions + operators

    @staticmethod
    async def get_all_conditions_by_parent_id(
        parent_id: int, db: AsyncSession
    ) -> list[ActionCondition | ActionConditionOperator]:
        operators = await db.exec(
            select(ActionConditionOperator).where(
                ActionConditionOperator.parent_id == parent_id
            )
        )
        operators = list(operators.all())

        conditions = await db.exec(
            select(ActionCondition).where(ActionCondition.parent_id == parent_id)
        )
        conditions = list(conditions.all())
        return conditions + operators

    @staticmethod
    def build_condition_tree(
        nodes: list[ActionCondition | ActionConditionOperator],
        parent: ActionConditionTreeNode | None = None,
    ) -> ActionConditionTreeNode:
        if parent is None:
            root = next(
                (
                    node
                    for node in nodes
                    if isinstance(node, ActionConditionOperator) and node.is_root()
                ),
                None,
            )
            if not root:
                raise ValueError("No root node found in the input")

            parent = root.to_tree_node()

        children = [
            node
            for node in nodes
            if node.parent_id == parent.node_id and parent.logical_operator is not None
        ]
        for child in children:
            parent.add_child(
                ActionConditionService.build_condition_tree(nodes, child.to_tree_node())
            )
        return parent

    @staticmethod
    async def create_condition_operator(
        condition_operator_request: ActionConditionOperatorRequest, db: AsyncSession
    ) -> ActionConditionOperator:
        condition_operator = ActionConditionOperator.model_validate(
            condition_operator_request
        )

        db.add(condition_operator)
        await db.commit()
        await db.refresh(condition_operator)
        return condition_operator

    @staticmethod
    async def create_condition_operator_root(
        operator_request: ActionConditionOperatorRequest, db: AsyncSession
    ) -> ActionConditionOperator:
        operator = ActionConditionOperator.model_validate(operator_request)

        db.add(operator)
        await db.commit()
        await db.refresh(operator)

        operator.root_id = operator.id

        if operator.action_id is not None:
            try:
                result = await ActionConditionService.get_all_conditions_by_action_id(
                    operator.action_id, db
                )
                root = next(
                    r
                    for r in result
                    if isinstance(r, ActionConditionOperator) and r.is_root()
                )
                raise ValueError(
                    f"Action with id {operator.action_id} already has root assigned to node {root}"  # noqa: E501
                )
            except NotFoundError:
                pass

        await db.commit()
        await db.refresh(operator)

        return operator

    @staticmethod
    async def create_condition(
        condition_request: ActionConditionRequest,
        db: AsyncSession,
        validate: bool = False,
    ) -> ActionCondition:
        condition = ActionCondition.model_validate(condition_request)

        if validate:
            if not await condition.validate_condition(db):
                raise ValueError("Condition is not valid")

        db.add(condition)
        await db.commit()
        await db.refresh(condition)
        return condition

    @staticmethod
    async def get_condition_operator_by_id(
        operator_id: int, db: AsyncSession
    ) -> ActionConditionOperator | None:
        return await db.get(ActionConditionOperator, operator_id)

    @staticmethod
    async def get_condition_by_id(
        condition_id: int, db: AsyncSession
    ) -> ActionCondition | None:
        return await db.get(ActionCondition, condition_id)

    @staticmethod
    async def get_conditions(db: AsyncSession) -> list[ActionCondition]:
        result = await db.exec(select(ActionCondition))
        return list(result.all())

    @staticmethod
    async def get_condition_operators(
        db: AsyncSession,
    ) -> list[ActionConditionOperator]:
        result = await db.exec(select(ActionConditionOperator))
        return list(result.all())

    @staticmethod
    async def assign_all_operators_by_root_to_action(
        root_id: int, action_id: int, db: AsyncSession
    ) -> (int, int):
        operators = await ActionConditionService.get_all_conditions_by_root_id(
            root_id, db
        )
        operators = [op for op in operators if isinstance(op, ActionConditionOperator)]

        for operator in operators:
            await ActionConditionService.assign_condition_operator_to_action(
                operator.id, action_id, db
            )

        return root_id, action_id

    @staticmethod
    async def assign_condition_operator_to_action(
        operator_id: int, action_id: int, db: AsyncSession
    ) -> (int, int):
        from app.services.action import ActionService

        operator = await ActionConditionService.get_condition_operator_by_id(
            operator_id, db
        )
        if not operator:
            raise NotFoundError(f"Operator with id {operator} not found")

        action = await ActionService.get_action_by_id(action_id, db)
        if not action:
            raise NotFoundError(f"Action with id {action_id} not found")

        operator.action_id = action.id
        db.add(operator)
        await db.commit()
        await db.refresh(operator)
        return operator.id, operator.action_id

    @staticmethod
    async def remove_all_operators_by_root_from_action(
        root_id: int, action_id: int, db: AsyncSession
    ) -> (int, int):
        operators = await ActionConditionService.get_all_conditions_by_root_id(
            root_id, db
        )
        operators = [op for op in operators if isinstance(op, ActionConditionOperator)]

        for operator in operators:
            await ActionConditionService.remove_condition_operator_from_action(
                operator.id, action_id, db
            )

        return root_id, action_id

    @staticmethod
    async def remove_condition_operator_from_action(
        operator_id: int, action_id: int, db: AsyncSession
    ) -> int:
        from app.services.action import ActionService

        operator = await ActionConditionService.get_condition_operator_by_id(
            operator_id, db
        )
        if not operator:
            raise NotFoundError(f"Operator with id {operator} not found")

        action = await ActionService.get_action_by_id(action_id, db)
        if not action:
            raise NotFoundError(f"Action with id {action_id} not found")

        operator.action_id = None
        db.add(operator)
        await db.commit()
        await db.refresh(operator)
        return operator.id

    @staticmethod
    async def update_condition(
        condition_id: int,
        condition_update: ActionConditionUpdateRequest,
        db: AsyncSession,
    ) -> ActionCondition:
        condition = await ActionConditionService.get_condition_by_id(condition_id, db)
        if not condition:
            raise NotFoundError(f"Condition with id {condition_id} not found")

        condition_update_data = condition_update.model_dump(exclude_unset=True)
        condition.sqlmodel_update(condition_update_data)

        db.add(condition)
        await db.commit()
        await db.refresh(condition)
        return condition

    @staticmethod
    async def update_condition_operator(
        operator_id: int,
        operator_update: ActionConditionOperatorUpdateRequest,
        db: AsyncSession,
    ) -> ActionConditionOperator:
        operator = await ActionConditionService.get_condition_operator_by_id(
            operator_id, db
        )
        if not operator:
            raise NotFoundError(f"Operator with id {operator_id} not found")

        operator_update_data = operator_update.model_dump(exclude_unset=True)
        operator.sqlmodel_update(operator_update_data)

        db.add(operator)
        await db.commit()
        await db.refresh(operator)
        return operator

    @staticmethod
    async def delete_condition_operator(
        operator_id: int, db: AsyncSession, cascade: bool = False
    ) -> None:
        operator = await ActionConditionService.get_condition_operator_by_id(
            operator_id, db
        )
        if not operator:
            raise NotFoundError(f"Operator with id {operator} not found")

        if cascade:
            children = await ActionConditionService.get_all_conditions_by_parent_id(
                operator.id, db
            )
            for child in children:
                if isinstance(child, ActionConditionOperator):
                    await ActionConditionService.delete_condition_operator(
                        child.id, db, True
                    )
                elif isinstance(child, ActionCondition):
                    await ActionConditionService.delete_condition(child.id, db)

        await db.delete(operator)
        await db.commit()

    @staticmethod
    async def delete_condition(condition_id: int, db: AsyncSession) -> None:
        condition = await ActionConditionService.get_condition_by_id(condition_id, db)
        if not condition:
            raise NotFoundError(f"Condition with id {condition_id} not found")

        await db.delete(condition)
        await db.commit()

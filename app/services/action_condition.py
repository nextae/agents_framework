from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.errors.api import ConflictError, NotFoundError
from app.models.action_condition import (
    ActionCondition,
    ActionConditionRequest,
    ActionConditionTreeNode,
    ActionConditionUpdateRequest,
)
from app.models.action_condition_operator import (
    ActionConditionOperator,
    ActionConditionOperatorRequest,
    ActionConditionOperatorUpdateRequest,
    NewConditionTreeRequest,
)
from app.services.action import ActionService


class ActionConditionService:
    @staticmethod
    async def try_get_root_for_action_id(
        action_id: int, db: AsyncSession
    ) -> ActionConditionOperator | None:
        operators = await db.exec(
            select(ActionConditionOperator).where(
                ActionConditionOperator.action_id == action_id
            )
        )
        operators = list(operators.all())
        root = [op for op in operators if op.is_root()]
        if len(root) == 0:
            return None
        if len(root) > 1:
            raise ConflictError(f"Found multiple roots for action_id: {action_id}")
        return root[0]

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
        root = await ActionConditionService.try_get_root_for_action_id(action_id, db)
        if root is None:
            return []

        operators = await db.exec(
            select(ActionConditionOperator).where(
                ActionConditionOperator.action_id == action_id
            )
        )
        operators = list(operators.all())

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

        await ActionConditionService.__check_parent_and_root(
            condition_operator.parent_id, condition_operator.root_id, db
        )

        action = await ActionService.get_action_by_id(condition_operator.action_id, db)
        if action is None:
            raise NotFoundError(
                f"Action with id {condition_operator.action_id} not found"
            )

        db.add(condition_operator)
        await db.commit()
        await db.refresh(condition_operator)
        return condition_operator

    @staticmethod
    async def create_condition_operator_root(
        tree_request: NewConditionTreeRequest, db: AsyncSession
    ) -> ActionConditionOperator:
        operator = ActionConditionOperator.model_validate(tree_request)

        if operator.action_id is not None:
            action = await ActionService.get_action_by_id(operator.action_id, db)
            if action is None:
                raise NotFoundError(f"Action with id {operator.action_id} not found")

            root = await ActionConditionService.try_get_root_for_action_id(
                operator.action_id, db
            )
            if root:
                raise ConflictError(
                    f"Action with id {operator.action_id} already has root assigned with id {root.id}"  # noqa: E501
                )

        db.add(operator)
        await db.commit()
        await db.refresh(operator)

        operator.root_id = operator.id

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

        await ActionConditionService.__check_parent_and_root(
            condition.parent_id, condition.root_id, db
        )

        if validate:
            if not await condition.validate_condition(db):
                raise ConflictError("Condition is not valid")

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
    ) -> tuple[int, int]:
        operator = await ActionConditionService.get_condition_operator_by_id(
            root_id, db
        )
        if operator is None:
            raise NotFoundError(f"Operator with id {root_id} not found")
        if not operator.is_root():
            raise ConflictError(f"Operator with id {root_id} is not a root")

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
    async def update_condition(
        condition_id: int,
        condition_update: ActionConditionUpdateRequest,
        db: AsyncSession,
    ) -> ActionCondition:
        condition = await ActionConditionService.get_condition_by_id(condition_id, db)
        if not condition:
            raise NotFoundError(f"Condition with id {condition_id} not found")

        await ActionConditionService.__check_parent_and_root(
            condition_update.parent_id, condition_update.root_id, db
        )

        condition_update_data = condition_update.model_dump(exclude_unset=True)
        condition.sqlmodel_update(condition_update_data)

        if not await condition.validate_condition(db):
            raise ConflictError("Condition is not valid")

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

        await ActionConditionService.__check_parent_and_root(
            operator_update.parent_id, operator_update.root_id, db
        )

        action = await ActionService.get_action_by_id(operator_update.action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {operator_update.action_id} not found")

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

    @staticmethod
    async def __check_parent_and_root(
        parent_id: int | None, root_id: int | None, db: AsyncSession
    ) -> None:
        if parent_id is not None:
            parent = await ActionConditionService.get_condition_operator_by_id(
                parent_id, db
            )
            if parent is None:
                raise NotFoundError(f"No operator with id {parent_id} found")

        root = await ActionConditionService.get_condition_operator_by_id(root_id, db)
        if root is None:
            raise NotFoundError(f"No root with id {root_id} found")
        if not root.is_root():
            raise ConflictError(f"Operator with id {root_id} is not a root")

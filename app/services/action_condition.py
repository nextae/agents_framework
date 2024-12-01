from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.action_condition import ActionCondition, ComparisonMethod
from app.models.action_condition_operator import (
    ActionConditionOperator,
    LogicalOperator,
)


class ActionConditionTreeNode:
    mock_state = {"number": "3", "name": "random", "fraction": "5.123123"}

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

    def evaluate_tree(self) -> bool:
        return self.root.__evaluate()

    def __evaluate(self) -> bool:
        if len(self.children) == 0:
            state_var = ActionConditionTreeNode.mock_state[self.state_variable_name]

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
            results = [child.__evaluate() for child in self.children]
            if self.logical_operator == LogicalOperator.AND:
                return all(results)
            return any(results)


class ActionConditionService:
    @staticmethod
    async def get_conditions_by_root(
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
    def build_condition_tree(
        nodes: list[ActionCondition | ActionConditionOperator],
        parent: ActionConditionTreeNode | None = None,
    ) -> ActionConditionTreeNode:
        if parent is None:
            root = next((node for node in nodes if node.id == node.root_id), None)
            if not root:
                raise ValueError("No root node found in the input")

            parent = root.to_tree_node()

        children = [node for node in nodes if node.parent_id == parent.node_id]
        for child in children:
            parent.add_child(
                ActionConditionService.build_condition_tree(nodes, child.to_tree_node())
            )
        return parent

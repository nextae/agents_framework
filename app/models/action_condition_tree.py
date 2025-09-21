import json

from app.errors.conditions import ConditionEvaluationError, StateVariableNotFoundError
from app.models.action_condition import ActionCondition, ComparisonMethod, LogicalOperator
from app.models.action_condition_operator import ActionConditionOperator
from app.models.agent import Agent
from app.models.global_state import GlobalState, State, StateValue


class ActionConditionTreeNode:
    node_id: int
    logical_operator: LogicalOperator | None
    comparison: ComparisonMethod | None
    state_variable_name: str | None
    expected_value: str | None
    state_agent_id: int | None
    children: list["ActionConditionTreeNode"]
    parent: "ActionConditionTreeNode"
    root: "ActionConditionTreeNode"

    def __init__(
        self,
        node_id: int,
        logical_operator: LogicalOperator | None = None,
        comparison: ComparisonMethod | None = None,
        state_variable_name: str | None = None,
        expected_value: str | None = None,
        state_agent_id: int | None = None,
    ):
        self.node_id = node_id
        self.logical_operator = logical_operator
        self.comparison = comparison
        self.state_agent_id = state_agent_id
        self.state_variable_name = state_variable_name
        self.expected_value = expected_value
        self.children = []
        self.parent = self
        self.root = self

    @classmethod
    def build(
        cls,
        parent: "ActionConditionTreeNode",
        conditions: list[ActionCondition],
        operators: list[ActionConditionOperator],
    ) -> "ActionConditionTreeNode":
        for condition in conditions:
            if condition.parent_id == parent.node_id:
                parent.add_child(cls.from_condition(condition))

        for operator in operators:
            if operator.parent_id == parent.node_id:
                parent.add_child(cls.build(cls.from_operator(operator), conditions, operators))

        return parent

    @classmethod
    def from_condition(cls, condition: ActionCondition) -> "ActionConditionTreeNode":
        return cls(
            node_id=condition.id,
            comparison=condition.comparison,
            state_variable_name=condition.state_variable_name,
            expected_value=condition.expected_value,
            state_agent_id=condition.state_agent_id,
        )

    @classmethod
    def from_operator(cls, operator: ActionConditionOperator) -> "ActionConditionTreeNode":
        return cls(node_id=operator.id, logical_operator=operator.logical_operator)

    def add_child(self, child: "ActionConditionTreeNode") -> None:
        self.children.append(child)
        child.parent = self
        child.root = self.root

    def is_operator(self) -> bool:
        return self.logical_operator is not None

    def _evaluate_operator(self, global_state: State, agent_states: dict[int, State]) -> bool:
        """Evaluate the logical operator node."""

        results = (child.evaluate(global_state, agent_states) for child in self.children)
        if self.logical_operator == LogicalOperator.AND:
            return all(results)
        else:
            return any(results)

    def _evaluate_condition(self, global_state: State, agent_states: dict[int, State]) -> bool:
        """Evaluate the condition leaf node."""

        state_var = self._get_state_variable(global_state, agent_states)

        try:
            expected_value = json.loads(self.expected_value)
        except json.JSONDecodeError:
            expected_value = self.expected_value

        try:
            match self.comparison:
                case ComparisonMethod.EQUAL:
                    return state_var == expected_value
                case ComparisonMethod.NOT_EQUAL:
                    return state_var != expected_value
                case ComparisonMethod.GREATER:
                    return state_var > expected_value
                case ComparisonMethod.LESS:
                    return state_var < expected_value
                case ComparisonMethod.AT_LEAST:
                    return state_var >= expected_value
                case ComparisonMethod.AT_MOST:
                    return state_var <= expected_value
                case _:
                    raise ConditionEvaluationError(f"Unknown comparison method: {self.comparison}")
        except TypeError:
            raise ConditionEvaluationError(
                f"Comparison '{self.comparison.name}' is not valid for values: "
                f"state_var={state_var}, expected_value={expected_value}"
            )

    def evaluate(self, global_state: State, agent_states: dict[int, State]) -> bool:
        """
        Evaluate the node.

        Args:
            global_state (State): The global state.
            agent_states (dict[int, State]): The states of agents by their IDs.

        Returns:
            bool: The result of the evaluation.
        """

        if self.is_operator():
            return self._evaluate_operator(global_state, agent_states)

        return self._evaluate_condition(global_state, agent_states)

    def _get_state_variable(
        self, global_state: State, agent_states: dict[int, State]
    ) -> StateValue:
        """Retrieve the state variable value based on the state_variable_name and state_agent_id."""

        if self.state_agent_id is None:
            state = global_state
        else:
            state = agent_states.get(self.state_agent_id)
            if state is None:
                raise ConditionEvaluationError(f"Agent with id {self.state_agent_id} not found")

        keys = self.state_variable_name.split("/")
        current = state

        try:
            for key in keys:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    current = current[int(key)]
                else:
                    raise StateVariableNotFoundError(
                        f"State variable name '{self.state_variable_name}' not found"
                    )
            return current
        except (KeyError, IndexError, ValueError, TypeError) as e:
            raise StateVariableNotFoundError(
                f"State variable name '{self.state_variable_name}' not found"
            ) from e


class ActionConditionTree:
    root: ActionConditionTreeNode
    global_state: State
    agent_states: dict[int, State]

    def __init__(
        self, root: ActionConditionTreeNode, global_state: GlobalState, agents: list[Agent]
    ) -> None:
        self.root = root
        self.global_state = global_state.state
        self.agent_states = {agent.id: agent.state for agent in agents}

    def evaluate(self) -> bool:
        return self.root.evaluate(self.global_state, self.agent_states)

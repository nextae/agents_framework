import json
from enum import Enum

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.errors.conditions import ConditionEvaluationError, StateVariableNotFoundError
from app.models.global_state import StateValue
from app.services.global_state import GlobalStateService


class ComparisonMethod(str, Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    AT_LEAST = ">="
    AT_MOST = "<="


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"


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
            except TypeError:
                raise ConditionEvaluationError(
                    f"Comparison '{self.comparison.name}' is not valid for values: "
                    f"state_var={state_var}, expected_value={self.expected_value}"
                )
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
        except ConditionEvaluationError:
            return False
        return True

    async def __get_state_variable(self, db: AsyncSession) -> StateValue:
        from app.services.agent import AgentService

        if self.state_variable_name.startswith("global"):
            state = (await GlobalStateService.get_state(db)).state
        elif self.state_variable_name.startswith("agent-"):
            agent_id = int(self.state_variable_name.split("/")[0].split("-")[1])
            agent = await AgentService.get_agent_by_id(agent_id, db)
            if agent is None:
                raise ConditionEvaluationError(f"Agent with id {agent_id} not found")
            state = agent.state
        else:
            raise ConditionEvaluationError(
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
                    raise StateVariableNotFoundError("State variable not found")
            return current
        except (KeyError, IndexError, ValueError, TypeError):
            raise StateVariableNotFoundError("State variable not found")


class ActionConditionBase(SQLModel):
    parent_id: int = Field(foreign_key="actionconditionoperator.id")
    root_id: int = Field(foreign_key="actionconditionoperator.id")
    state_variable_name: str
    comparison: ComparisonMethod = Field(
        sa_column=Column(SAEnum(ComparisonMethod, native_enum=False), nullable=False)
    )
    expected_value: str


class ActionCondition(ActionConditionBase, table=True):
    id: int = Field(default=None, primary_key=True)

    async def validate_condition(self, db: AsyncSession) -> bool:
        tree_node = self.to_tree_node()
        return await tree_node.validate_leaf(db)

    def to_tree_node(self) -> ActionConditionTreeNode:
        return ActionConditionTreeNode(
            self.id,
            None,
            self.comparison,
            self.state_variable_name,
            self.expected_value,
        )


class ActionConditionRequest(ActionConditionBase):
    pass


class ActionConditionUpdateRequest(SQLModel):
    parent_id: int | None = None
    root_id: int | None = None
    state_variable_name: str | None = None
    comparison: ComparisonMethod | None = None
    expected_value: str | None = None


class ActionConditionResponse(ActionConditionBase):
    id: int

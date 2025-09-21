import json

import streamlit_flow as sf
from pydantic import BaseModel, Field, field_serializer

from app.models.action import ActionResponse
from app.models.action_condition import ActionConditionResponse, ComparisonMethod
from app.models.action_condition_operator import (
    ActionConditionOperatorResponse,
    LogicalOperator,
)
from app.models.action_param import ActionParamResponse, ActionParamType, LiteralValue
from app.models.agent import AgentResponse
from app.models.agent_message import ActionResponseDict
from app.models.player import PlayerResponse

__all__ = (
    "AgentForm",
    "Agent",
    "ActionParamForm",
    "ActionParam",
    "ActionForm",
    "Action",
    "Player",
    "Condition",
    "Operator",
    "CallerMessage",
    "AgentMessage",
)


class AgentForm(BaseModel):
    id: int = Field(..., title="ID", readOnly=True)
    name: str = Field(..., description="The name of the agent.")
    description: str = Field(..., description="A description of the agent.", format="multi-line")
    instructions: str = Field(..., description="Instructions for the agent.", format="multi-line")


class Agent(AgentForm):
    actions_ids: list[int]

    @classmethod
    def from_response(cls, response: AgentResponse) -> "Agent":
        return cls(
            id=response.id,
            name=response.name,
            description=response.description or "",
            instructions=response.instructions,
            actions_ids=[action.id for action in response.actions],
        )

    def to_form_model(self) -> AgentForm:
        return AgentForm.model_validate(self.model_dump())


class ActionParamForm(BaseModel):
    id: int = Field(..., title="ID", readOnly=True)
    name: str = Field(..., description="The name of the parameter.")
    description: str = Field(
        ..., description="The description of the parameter.", format="multi-line"
    )
    type: ActionParamType = Field(..., description="The type of the parameter.")

    @field_serializer("type")
    def serialize_type(self, param_type: ActionParamType) -> str:
        return param_type.value


class ActionParam(ActionParamForm):
    literal_values: list[LiteralValue] | None

    @classmethod
    def from_response(cls, response: ActionParamResponse) -> "ActionParam":
        return cls(
            id=response.id,
            name=response.name,
            description=response.description,
            type=response.type,
            literal_values=response.literal_values,
        )

    def to_form_model(self) -> ActionParamForm:
        return ActionParamForm.model_validate(self.model_dump())


class ActionForm(BaseModel):
    id: int = Field(..., title="ID", readOnly=True)
    name: str = Field(..., description="The name of the action.")
    description: str = Field(..., description="The description of the action.", format="multi-line")


class Action(ActionForm):
    triggered_agent_id: int | None
    params: list[ActionParam]

    @classmethod
    def from_response(cls, response: ActionResponse) -> "Action":
        return cls(
            id=response.id,
            name=response.name,
            description=response.description or "",
            triggered_agent_id=response.triggered_agent_id,
            params=[ActionParam.from_response(param) for param in response.params],
        )

    def to_form_model(self) -> ActionForm:
        return ActionForm.model_validate(self.model_dump())


class Player(BaseModel):
    id: int = Field(..., title="ID", readOnly=True)
    name: str = Field(..., description="The name of the player.")
    description: str = Field(
        ...,
        description=(
            "Description of the player.\n\nThis is what agents will know about this player."
        ),
        format="multi-line",
    )

    @classmethod
    def from_response(cls, response: PlayerResponse) -> "Player":
        return cls(id=response.id, name=response.name, description=response.description or "")


class Condition(BaseModel):
    id: int = Field(default=0, title="ID", readOnly=True)
    root_id: int = Field(default=0, title="Root ID")
    parent_id: int = Field(default=0, title="Parent ID")
    state_agent_id: int | None = Field(default=None, title="State Agent ID")
    state_variable_name: str
    comparison: ComparisonMethod
    expected_value: str

    @classmethod
    def from_response(cls, response: ActionConditionResponse) -> "Condition":
        return cls.model_validate(response.model_dump())

    def is_expected_value_text(self) -> bool:
        """Check if the expected value is text or JSON."""

        try:
            json.loads(self.expected_value)
            return False
        except json.JSONDecodeError:
            return True

    def to_node(
        self,
        node_id: str | None = None,
        position: tuple[int, int] = (90, 60),
        agent: Agent | None = None,
    ) -> sf.StreamlitFlowNode:
        data = self.model_dump()

        expected_value = (
            self.expected_value if not self.is_expected_value_text() else f'"{self.expected_value}"'
        )
        is_valid = (
            self.state_agent_id is None
            and agent is None
            or (agent is not None and agent.id == self.state_agent_id)
        )
        state_text = (
            ("Global" if agent is None else f"Agent: {agent.name}")
            if is_valid
            else "Agent not found!"
        )
        data["content"] = (
            f"{self.state_variable_name} {self.comparison.value} {expected_value}"
            f'<p style="color: {"#9FA7BC" if is_valid else "#ED4337"}">{state_text}</p>'
        )
        data["type"] = "condition"
        return sf.StreamlitFlowNode(
            id=node_id or f"condition_{self.id}",
            pos=position,
            data=data,
            node_type="output",
            style={"background": "#333949", "color": "white"},
            connectable=True,
        )

    def to_edge(self) -> sf.StreamlitFlowEdge:
        return sf.StreamlitFlowEdge(
            id=f"condition_edge_{self.id}",
            source=f"operator_{self.parent_id}",
            target=f"condition_{self.id}",
            animated=True,
            deletable=True,
        )


class Operator(BaseModel):
    id: int = Field(default=0, title="ID", readOnly=True)
    root_id: int = Field(default=0, title="Root ID")
    parent_id: int | None = Field(default=0, title="Parent ID")
    action_id: int = Field(default=0, title="Action ID")
    logical_operator: LogicalOperator

    @classmethod
    def from_response(cls, response: ActionConditionOperatorResponse) -> "Operator":
        return cls.model_validate(response.model_dump())

    def is_root(self) -> bool:
        return self.parent_id is None

    def to_node(
        self, node_id: str | None = None, position: tuple[int, int] = (90, 60)
    ) -> sf.StreamlitFlowNode:
        data = self.model_dump()
        data["content"] = self.logical_operator.value
        data["type"] = "operator"
        return sf.StreamlitFlowNode(
            id=node_id or f"operator_{self.id}",
            pos=position,
            data=data,
            node_type="input" if self.is_root() else "default",
            style={
                "background": "#333949" if not self.is_root() else "#212530",
                "color": "white",
                "width": "50px",
                "height": "50px",
                "display": "flex",
                "justify-content": "center",
                "align-items": "center",
            },
            connectable=True,
        )

    def to_edge(self) -> sf.StreamlitFlowEdge:
        return sf.StreamlitFlowEdge(
            id=f"operator_edge_{self.id}",
            source=f"operator_{self.parent_id}",
            target=f"operator_{self.id}",
            animated=True,
            deletable=True,
        )


class CallerMessage(BaseModel):
    caller: Player | Agent
    query: str


class AgentMessage(BaseModel):
    agent: Agent
    response: str
    actions: list[ActionResponseDict]

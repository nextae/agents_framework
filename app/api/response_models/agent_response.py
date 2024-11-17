from dataclasses import dataclass

from app.api.response_models import ActionResponse
from app.models.agent import Agent
from app.models.agent_message import AgentMessage


@dataclass
class AgentResponse:
    agent: Agent
    messages: list[AgentMessage]
    actions: list[ActionResponse]

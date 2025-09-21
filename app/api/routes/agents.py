from fastapi import APIRouter, Depends

from app.api.dependencies import validate_token
from app.errors.api import NotFoundError
from app.models import AgentMessage
from app.models.agent import Agent, AgentRequest, AgentResponse, AgentUpdateRequest
from app.services.agent_service import AgentService

agents_router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(validate_token)])


@agents_router.get("", response_model=list[AgentResponse])
async def get_agents() -> list[Agent]:
    return await AgentService().get_agents()


@agents_router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int) -> Agent:
    agent = await AgentService().get_agent_by_id(agent_id)
    if agent is None:
        raise NotFoundError(f"Agent with id {agent_id} not found")

    return agent


@agents_router.post("", status_code=201, response_model=AgentResponse)
async def create_agent(agent_request: AgentRequest) -> Agent:
    return await AgentService().create_agent(agent_request)


@agents_router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, agent_update_request: AgentUpdateRequest) -> Agent:
    return await AgentService().update_agent(agent_id, agent_update_request)


@agents_router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: int) -> None:
    await AgentService().delete_agent(agent_id)


@agents_router.get("/{agent_id}/messages")
async def get_agent_messages(agent_id: int) -> list[AgentMessage]:
    return await AgentService().get_agent_messages(agent_id)


@agents_router.delete("/{agent_id}/messages", status_code=204)
async def delete_agent_messages(agent_id: int) -> None:
    await AgentService().delete_agent_messages(agent_id)


@agents_router.post("/{agent_id}/actions/{action_id}/assign", response_model=AgentResponse)
async def assign_action(agent_id: int, action_id: int) -> Agent:
    return await AgentService().assign_action_to_agent(agent_id, action_id)


@agents_router.post("/{agent_id}/actions/{action_id}/remove", response_model=AgentResponse)
async def remove_action(agent_id: int, action_id: int) -> Agent:
    return await AgentService().remove_action_from_agent(agent_id, action_id)

from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_db
from app.errors.api import NotFoundError
from app.models import AgentMessage
from app.models.agent import Agent, AgentRequest, AgentResponse, AgentUpdateRequest
from app.models.agents_actions_match import AgentsActionsMatch
from app.services.agent import AgentService

agents_router = APIRouter(prefix="/agents")


@agents_router.get("", response_model=list[AgentResponse])
async def get_agents(db: AsyncSession = Depends(get_db)) -> list[Agent]:
    return await AgentService.get_agents(db)


@agents_router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)) -> Agent:
    agent = await AgentService.get_agent_by_id(agent_id, db)
    if agent is None:
        raise NotFoundError(f"Agent with id {agent_id} not found")

    return agent


@agents_router.post("", status_code=201)
async def create_agent(
    agent_create: AgentRequest, db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    agent = await AgentService.create_agent(agent_create, db)

    return AgentResponse.model_validate(
        agent, update={"actions": [], "conversation_history": []}
    )


@agents_router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int, agent_update: AgentUpdateRequest, db: AsyncSession = Depends(get_db)
) -> Agent:
    return await AgentService.update_agent(agent_id, agent_update, db)


@agents_router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: int, db: AsyncSession = Depends(get_db)) -> None:
    return await AgentService.delete_agent(agent_id, db)


@agents_router.get("/{agent_id}/messages")
async def get_agent_messages(
    agent_id: int, db: AsyncSession = Depends(get_db)
) -> list[AgentMessage]:
    return await AgentService.get_agent_messages(agent_id, db)


@agents_router.delete("/{agent_id}/messages", status_code=204)
async def delete_agent_messages(
    agent_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    return await AgentService.delete_agent_messages(agent_id, db)


@agents_router.post("/assign_action", response_model=AgentsActionsMatch)
async def assign_action(
    agent_id: int, action_id: int, db: AsyncSession = Depends(get_db)
) -> AgentsActionsMatch:
    return await AgentService.assign_action_to_agent(agent_id, action_id, db)


@agents_router.post("/remove_action")
async def remove_action(
    agent_id: int, action_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    return await AgentService.remove_action_from_agent(agent_id, action_id, db)

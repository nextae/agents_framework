from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.response_models import ActionResponse, AgentResponse
from app.db.database import get_db
from app.models.agent import Agent
from app.models.agent_message import AgentMessage
from app.models.agents_actions_matches import AgentsActionsMatches
from app.services.agent import AgentService

agents_router = APIRouter(prefix="/agents")


@agents_router.get("/", response_model=list[AgentResponse])
async def get_agents(db: AsyncSession = Depends(get_db)) -> list[AgentResponse]:
    agents = await AgentService.get_agents(db)
    resp = []
    for agent in agents:
        actions = []
        for action in agent.actions:
            actions.append(ActionResponse(action, action.params))
        resp.append(AgentResponse(agent, agent.conversation_history, actions))

    return resp


@agents_router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await AgentService.get_agent_by_id(agent_id, db)
    actions = []
    for action in agent.actions:
        actions.append(ActionResponse(action, action.params))
    resp = AgentResponse(agent, agent.conversation_history, actions)
    return resp


@agents_router.post("/", response_model=AgentResponse)
async def create_agent(
    agent: Agent, db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    agent = await AgentService.create_agent(agent, db)
    return AgentResponse(agent, [], [])


@agents_router.put("/update_agent/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int, agent: Agent, db: AsyncSession = Depends(get_db)
) -> AgentResponse:
    return await AgentService.update_agent(agent_id, agent, db)


@agents_router.post("/assign_action", response_model=AgentsActionsMatches)
async def assign_action(
    agent_id: int, action_id: int, db: AsyncSession = Depends(get_db)
) -> AgentsActionsMatches:
    return await AgentService.assign_action_to_agent(agent_id, action_id, db)


@agents_router.post("/remove_action", response_model=tuple[int, int])
async def remove_action(
    agent_id: int, action_id: int, db: AsyncSession = Depends(get_db)
):
    return await AgentService.remove_action_from_agent(agent_id, action_id, db)


@agents_router.post(
    "/add_message/{agent_id}", response_model=AgentResponse
)  # TODO datetime doesn't work :(
async def add_message_to_agent(
    agent_id: int, message: AgentMessage, db: AsyncSession = Depends(get_db)
):
    return await AgentService.create_agent_message(agent_id, message, db)

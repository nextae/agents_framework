from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.database import get_db
from app.models.agent import Agent
from app.services.agent import AgentService

agents_router = APIRouter(prefix="/agents")


@agents_router.get("/", response_model=list[Agent])
async def get_agents(db: Session = Depends(get_db)) -> list[Agent]:
    return await AgentService.get_agents(db)


@agents_router.get("/{agent_id}", response_model=list[Agent])
async def get_agent(agent_id: int, db: Session = Depends(get_db)) -> Agent:
    return await AgentService.get_agent(agent_id, db)


@agents_router.post("/", response_model=Agent)
async def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    return await AgentService.create_agent(agent, db)

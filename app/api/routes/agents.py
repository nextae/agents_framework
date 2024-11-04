from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.database import get_db
from app.models.agent import Agent

agents_router = APIRouter(prefix="/agents")


@agents_router.get("/", response_model=list[Agent])
async def get_agents(db: Session = Depends(get_db)) -> list[Agent]:
    stmt = select(Agent)
    result = db.exec(stmt).fetchall()
    return list(result)


@agents_router.post("/", response_model=Agent)
async def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.database import get_db
from app.models.action import Action
from app.models.agent import Agent

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def index():
    return {"message": "Hello World from router"}


@api_router.get("/agents", response_model=list[Agent])
async def get_agents(db: Session = Depends(get_db)) -> list[Agent]:
    stmt = select(Agent)
    result = db.exec(stmt).fetchall()
    return list(result)


@api_router.post("/agents", response_model=Agent)
async def create_agent(agent: Agent, db: Session = Depends(get_db)) -> Agent:
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@api_router.get("/actions", response_model=list[Action])
async def get_actions(db: Session = Depends(get_db)) -> list[Action]:
    stmt = select(Action)
    result = db.exec(stmt).fetchall()
    return list(result)


@api_router.post("/actions", response_model=Action)
async def create_action(action: Action, db: Session = Depends(get_db)) -> Action:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

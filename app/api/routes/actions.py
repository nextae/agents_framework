from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db.database import get_db
from app.models.action import Action

actions_router = APIRouter(prefix="/actions")


@actions_router.get("/", response_model=list[Action])
async def get_actions(db: Session = Depends(get_db)) -> list[Action]:
    stmt = select(Action)
    result = db.exec(stmt).fetchall()
    return list(result)


@actions_router.post("/", response_model=Action)
async def create_action(action: Action, db: Session = Depends(get_db)) -> Action:
    db.add(action)
    db.commit()
    db.refresh(action)
    return action

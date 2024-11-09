from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db.database import get_db
from app.models.action import Action
from app.models.action_param import ActionParam
from app.services.action import ActionService

actions_router = APIRouter(prefix="/actions")


@actions_router.get("/", response_model=list[Action])
async def get_actions(db: Session = Depends(get_db)) -> list[Action]:
    return await ActionService.get_actions(db)


@actions_router.get("/{action_id}/params", response_model=list[ActionParam])
async def get_action_params(action_id: int, db: Session = Depends(get_db)):
    action = await ActionService.get_action(action_id, db)
    return action.params


@actions_router.get("/{action_id}", response_model=Action)
async def get_action(action_id: int, db: Session = Depends(get_db)) -> Action:
    return await ActionService.get_action(action_id, db)


@actions_router.post("/", response_model=Action)
async def create_action(action: Action, db: Session = Depends(get_db)) -> Action:
    return await ActionService.create_action(action, db)

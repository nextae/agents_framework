from fastapi import APIRouter

from app.api.routes.action_condition import condition_router
from app.api.routes.actions import actions_router
from app.api.routes.agents import agents_router
from app.api.routes.params import params_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(agents_router)
api_router.include_router(actions_router)
api_router.include_router(params_router)
api_router.include_router(condition_router)

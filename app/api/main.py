from fastapi import APIRouter

from app.api.routes.actions import actions_router
from app.api.routes.agents import agents_router
from app.api.routes.auth import auth_router
from app.api.routes.conditions import conditions_router
from app.api.routes.params import params_router
from app.api.routes.players import players_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(agents_router)
api_router.include_router(actions_router)
api_router.include_router(params_router)
api_router.include_router(conditions_router)
api_router.include_router(players_router)
api_router.include_router(auth_router)

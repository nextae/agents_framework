from fastapi import APIRouter

from app.api.routes.actions import actions_router
from app.api.routes.agents import agents_router

api_router = APIRouter(prefix="/api")
api_router.include_router(agents_router)
api_router.include_router(actions_router)


@api_router.get("/")
async def index():
    return {"message": "Hello World from router"}

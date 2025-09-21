from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Action, Agent

from .base_repository import BaseRepository


class AgentRepository(BaseRepository[Agent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Agent)

    async def find_by_id(self, agent_id: int) -> Agent | None:
        return await self._session.get(Agent, agent_id, populate_existing=True)

    async def find_populated_by_id(self, agent_id: int) -> Agent | None:
        return await self._session.get(
            Agent,
            agent_id,
            options=[
                selectinload(Agent.conversation_history),
                selectinload(Agent.actions).selectinload(Action.triggered_agent),
            ],
            populate_existing=True,
        )

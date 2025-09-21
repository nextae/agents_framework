from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Action

from .base_repository import BaseRepository


class ActionRepository(BaseRepository[Action]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Action)

    async def find_first_by_triggered_agent_id(self, agent_id: int) -> Action | None:
        result = await self._session.exec(
            select(Action).where(Action.triggered_agent_id == agent_id)
        )
        return result.first()

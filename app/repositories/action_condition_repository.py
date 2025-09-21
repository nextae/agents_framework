from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ActionCondition

from .base_repository import BaseRepository


class ActionConditionRepository(BaseRepository[ActionCondition]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionCondition)

    async def find_all_by_root_id(self, root_id: int) -> list[ActionCondition]:
        result = await self._session.exec(
            select(ActionCondition).where(ActionCondition.root_id == root_id)
        )
        return list(result.all())

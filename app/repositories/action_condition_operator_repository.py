from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ActionConditionOperator

from .base_repository import BaseRepository


class ActionConditionOperatorRepository(BaseRepository[ActionConditionOperator]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionConditionOperator)

    async def find_root_by_action_id(self, action_id: int) -> ActionConditionOperator | None:
        result = await self._session.exec(
            select(ActionConditionOperator)
            .where(ActionConditionOperator.action_id == action_id)
            .where(ActionConditionOperator.id == ActionConditionOperator.root_id)
            .limit(1)
        )
        return result.first()

    async def find_all_by_root_id(self, root_id: int) -> list[ActionConditionOperator]:
        result = await self._session.exec(
            select(ActionConditionOperator).where(ActionConditionOperator.root_id == root_id)
        )
        return list(result.all())

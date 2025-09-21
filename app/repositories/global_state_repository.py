from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import GlobalState

from .base_repository import BaseRepository


class GlobalStateRepository(BaseRepository[GlobalState]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, GlobalState)

    async def update(self, model: GlobalState) -> GlobalState:
        try:
            model = await self._session.merge(model)
            await self._session.flush()
            await self._session.refresh(model)
            return model
        except IntegrityError:
            await self._session.rollback()
            raise

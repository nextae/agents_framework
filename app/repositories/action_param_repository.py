from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import ActionParam

from .base_repository import BaseRepository


class ActionParamRepository(BaseRepository[ActionParam]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionParam)

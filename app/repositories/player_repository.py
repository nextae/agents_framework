from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Player

from .base_repository import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Player)

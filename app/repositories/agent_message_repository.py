from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import AgentMessage

from .base_repository import BaseRepository


class AgentMessageRepository(BaseRepository[AgentMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AgentMessage)

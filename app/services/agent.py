from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.agent import Agent


class AgentService:
    @staticmethod
    async def get_agents(db: AsyncSession) -> list[Agent]:
        stmt = select(Agent)
        result = (await db.exec(stmt)).fetchall()
        return list(result)

    @staticmethod
    async def get_agent(agent_id: int, db: AsyncSession) -> Agent | None:
        return await db.get(Agent, agent_id)

    @staticmethod
    async def create_agent(agent: Agent, db: AsyncSession):
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

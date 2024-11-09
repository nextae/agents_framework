from sqlmodel import Session, select

from app.models.agent import Agent


class AgentService:
    @staticmethod
    async def get_agents(db: Session) -> list[Agent]:
        stmt = select(Agent)
        result = db.exec(stmt).fetchall()
        return list(result)

    @staticmethod
    async def get_agent(agent_id: int, db: Session) -> Agent | None:
        return db.get(Agent, agent_id)

    @staticmethod
    async def create_agent(agent: Agent, db: Session):
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

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
        stmt = select(Agent).where(Agent.id == agent_id)
        result = db.exec(stmt).fetchall()
        if len(result) == 0:
            return None
        if len(result) == 1:
            return result[0]
        raise Exception(
            f"Found more than one agent with id {agent_id}. This shouldn't happen"
        )

    @staticmethod
    async def create_agent(agent: Agent, db: Session):
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

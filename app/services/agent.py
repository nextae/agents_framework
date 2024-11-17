from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.agent import Agent
from app.models.agent_message import AgentMessage
from app.models.agents_actions_matches import AgentsActionsMatches
from app.services.action import ActionService


class AgentService:
    @staticmethod
    async def get_agents(db: AsyncSession) -> list[Agent]:
        stmt = (
            select(Agent).options(
                selectinload(Agent.actions),
                selectinload(Agent.conversation_history),
            )  # TODO load actions and params
        )
        agents = (await db.exec(stmt)).fetchall()
        return list(agents)

    @staticmethod
    async def get_agent_by_id(agent_id: int, db: AsyncSession) -> Agent | None:
        stmt = (  # TODO load actions and params
            select(Agent)
            .options(
                selectinload(Agent.actions), selectinload(Agent.conversation_history)
            )
            .where(Agent.id == agent_id)
        )
        agent = (await db.exec(stmt)).first()
        return agent

    @staticmethod
    async def create_agent(agent: Agent, db: AsyncSession):
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def assign_action_to_agent(agent_id: int, action_id: int, db: AsyncSession):
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise ValueError(f"Agent with id={agent_id} does not exist")

        action = await ActionService.get_action_by_id(action_id, db)
        if action is None:
            raise ValueError(f"Action with id={action_id} does not exist")

        match = await db.get(AgentsActionsMatches, (agent_id, action.id))
        if match is not None:
            raise ValueError(
                f"Action with id={action_id} has already been assigned to agent with id={agent_id}"  # noqa: E501
            )

        match = AgentsActionsMatches()
        match.agent_id = agent_id
        match.action_id = action_id
        db.add(match)
        await db.commit()
        return match

    @staticmethod
    async def remove_action_from_agent(agent_id: int, action_id: int, db: AsyncSession):
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise ValueError(f"Agent with id={agent_id} does not exist")

        action = await ActionService.get_action_by_id(action_id, db)
        if action is None:
            raise ValueError(f"Action with id={action_id} does not exist")

        match = await db.get(AgentsActionsMatches, (agent_id, action.id))
        if match is None:
            raise ValueError(
                f"Action with id={action_id} hasn't been assigned to agent with id={agent_id}"  # noqa: E501
            )

        await db.delete(match)
        await db.commit()
        return agent_id, action_id

    @staticmethod
    async def update_agent(agent_id: int, updated: Agent, db: AsyncSession):
        old_agent = await AgentService.get_agent_by_id(agent_id, db)
        if old_agent is None:
            raise ValueError(f"Agent with id={agent_id} does not exist")

        old_agent.name = updated.name
        old_agent.description = updated.description

        await db.commit()
        await db.refresh(old_agent)
        return old_agent

    @staticmethod
    async def create_agent_message(
        agent_id: int, message: AgentMessage, db: AsyncSession
    ):
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise ValueError(f"Agent with id={agent_id} does not exist")

        db.add(message)
        await db.commit()

        agent.conversation_history.append(message)
        await db.refresh(agent)

        return agent

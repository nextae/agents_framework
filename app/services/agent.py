from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.errors import NotFoundError
from app.models.action import Action
from app.models.agent import Agent, AgentRequest, AgentUpdateRequest
from app.models.agent_message import AgentMessage
from app.models.agents_actions_match import AgentsActionsMatch
from app.models.global_state import State
from app.services.action import ActionService

LOAD_OPTIONS = [
    selectinload(Agent.actions).selectinload(Action.params),
    selectinload(Agent.actions).selectinload(Action.conditions),
    selectinload(Agent.conversation_history),
]


class AgentService:
    @staticmethod
    async def get_agents(db: AsyncSession) -> list[Agent]:
        result = await db.exec(select(Agent).options(*LOAD_OPTIONS))
        return list(result.all())

    @staticmethod
    async def get_agent_by_id(agent_id: int, db: AsyncSession) -> Agent | None:
        return await db.get(Agent, agent_id, options=LOAD_OPTIONS)

    @staticmethod
    async def create_agent(agent_request: AgentRequest, db: AsyncSession) -> Agent:
        agent = Agent.model_validate(agent_request)
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def assign_action_to_agent(
        agent_id: int, action_id: int, db: AsyncSession
    ) -> AgentsActionsMatch:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise NotFoundError(f"Agent with id {agent_id} does not exist")

        action = await ActionService.get_action_by_id(action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {action_id} does not exist")

        match = await db.get(AgentsActionsMatch, (agent_id, action.id))
        if match is not None:
            raise ValueError(
                f"Action with id {action_id} has already been assigned to agent with id {agent_id}"  # noqa: E501
            )

        match = AgentsActionsMatch(agent_id=agent_id, action_id=action_id)
        db.add(match)
        await db.commit()
        return match

    @staticmethod
    async def remove_action_from_agent(
        agent_id: int, action_id: int, db: AsyncSession
    ) -> None:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise NotFoundError(f"Agent with id {agent_id} does not exist")

        action = await ActionService.get_action_by_id(action_id, db)
        if action is None:
            raise NotFoundError(f"Action with id {action_id} does not exist")

        match = await db.get(AgentsActionsMatch, (agent_id, action.id))
        if match is None:
            raise NotFoundError(
                f"Action with id {action_id} hasn't been assigned to agent with id {agent_id}"  # noqa: E501
            )

        await db.delete(match)
        await db.commit()

    @staticmethod
    async def update_agent(
        agent_id: int, agent_update: AgentUpdateRequest, db: AsyncSession
    ) -> Agent:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise NotFoundError(f"Agent with id={agent_id} does not exist")

        agent_update_data = agent_update.model_dump(exclude_unset=True)
        agent.sqlmodel_update(agent_update_data)

        await db.commit()
        await db.refresh(agent)
        return agent

    @staticmethod
    async def delete_agent(agent_id: int, db: AsyncSession) -> None:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if not agent:
            raise NotFoundError(f"Agent with id {agent_id} not found")

        await db.delete(agent)
        await db.commit()

    @staticmethod
    async def create_agent_message(
        agent_id: int, message: AgentMessage, db: AsyncSession
    ) -> Agent:
        agent = await AgentService.get_agent_by_id(agent_id, db)
        if agent is None:
            raise NotFoundError(f"Agent with id {agent_id} does not exist")

        db.add(message)
        await db.commit()

        agent.conversation_history.append(message)
        await db.refresh(agent)

        return agent

    @staticmethod
    async def update_agent_state(agent: Agent, state: State, db: AsyncSession) -> Agent:
        agent.state = state
        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent

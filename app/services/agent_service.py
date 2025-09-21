from app.errors.api import ConflictError, NotFoundError
from app.models.agent import Agent, AgentRequest, AgentUpdateRequest
from app.models.agent_message import AgentMessage
from app.models.global_state import State

from .base_service import BaseService


class AgentService(BaseService):
    async def get_agents(self) -> list[Agent]:
        """
        Get all agents.

        Returns:
            list[Agent]: A list of all agents
        """

        async with self.unit_of_work as uow:
            return await uow.agents.find_all()

    async def get_agent_by_id(self, agent_id: int) -> Agent | None:
        """
        Get an agent by its ID.

        Args:
            agent_id (int): The ID of the agent to retrieve.

        Returns:
            Agent | None: The agent with the specified ID, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.agents.find_by_id(agent_id)

    async def get_populated_agent(self, agent_id: int) -> Agent | None:
        """
        Get an agent with its conversation history and actions relationships fully populated.

        Args:
            agent_id (int): The ID of the agent to retrieve.

        Returns:
            Agent | None: The agent with the specified ID, or None if not found.
        """

        async with self.unit_of_work as uow:
            return await uow.agents.find_populated_by_id(agent_id)

    async def create_agent(self, agent_request: AgentRequest) -> Agent:
        """
        Create a new agent.

        Args:
            agent_request (AgentRequest): The request to create the new agent.

        Returns:
            Agent: The created agent.
        """

        async with self.unit_of_work as uow:
            return await uow.agents.create(Agent.model_validate(agent_request))

    async def assign_action_to_agent(self, agent_id: int, action_id: int) -> Agent:
        """
        Assign an action to an agent.

        Args:
            agent_id (int): The ID of the agent to assign the action to.
            action_id (int): The ID of the action to assign to the agent.

        Returns:
            Agent: The updated agent with the assigned action.
        """

        async with self.unit_of_work as uow:
            agent = await self.get_agent_by_id(agent_id)
            if agent is None:
                raise NotFoundError(f"Agent with id {agent_id} not found")

            action = await uow.actions.find_by_id(action_id)
            if action is None:
                raise NotFoundError(f"Action with id {action_id} not found")

            if action in agent.actions:
                raise ConflictError(
                    f"Action with id {action_id} has already been assigned to agent with id {agent_id}"  # noqa: E501
                )

            agent.actions.append(action)
            return await uow.agents.update(agent)

    async def remove_action_from_agent(self, agent_id: int, action_id: int) -> Agent:
        """
        Remove an action from an agent.

        Args:
            agent_id (int): The ID of the agent to remove the action from.
            action_id (int): The ID of the action to remove from the agent.

        Returns:
            Agent: The updated agent with the action removed.
        """

        async with self.unit_of_work as uow:
            agent = await self.get_agent_by_id(agent_id)
            if agent is None:
                raise NotFoundError(f"Agent with id {agent_id} not found")

            action = await uow.actions.find_by_id(action_id)
            if action is None:
                raise NotFoundError(f"Action with id {action_id} not found")

            if action not in agent.actions:
                raise ConflictError(
                    f"Action with id {action.id} hasn't been assigned to agent with id {agent.id}"
                )

            agent.actions.remove(action)
            return await uow.agents.update(agent)

    async def update_agent(self, agent_id: int, agent_update_request: AgentUpdateRequest) -> Agent:
        """
        Update an existing agent.

        Args:
            agent_id (int): The ID of the agent to update.
            agent_update_request (AgentUpdateRequest): The request to update the agent.

        Returns:
            Agent: The updated agent.
        """

        async with self.unit_of_work as uow:
            agent = await self.get_agent_by_id(agent_id)
            if agent is None:
                raise NotFoundError(f"Agent with id {agent_id} not found")

            agent_update_data = agent_update_request.model_dump(exclude_unset=True)
            agent.sqlmodel_update(agent_update_data)

            return await uow.agents.update(agent)

    async def delete_agent(self, agent_id: int) -> None:
        """
        Delete an agent by its ID.

        Args:
            agent_id (int): The ID of the agent to delete.
        """

        async with self.unit_of_work as uow:
            agent = await self.get_agent_by_id(agent_id)
            if not agent:
                return None

            if await uow.actions.find_first_by_triggered_agent_id(agent_id) is not None:
                raise ConflictError(f"Agent with id {agent_id} has existing trigger actions")

            await uow.agents.delete(agent)

    async def add_agent_message(self, message: AgentMessage) -> AgentMessage:
        """
        Add a message to an agent's conversation history.

        Args:
            message (AgentMessage): The message to add.

        Returns:
            AgentMessage: The added message.
        """

        async with self.unit_of_work as uow:
            return await uow.messages.create(message)

    async def get_agent_messages(self, agent_id: int) -> list[AgentMessage]:
        """
        Get all messages from an agent's conversation history.

        Args:
            agent_id (int): The ID of the agent whose messages to retrieve.

        Returns:
            list[AgentMessage]: A list of messages from the agent's conversation history.
        """

        agent = await self.get_populated_agent(agent_id)
        if agent is None:
            raise NotFoundError(f"Agent with id {agent_id} not found")

        return agent.conversation_history

    async def delete_agent_messages(self, agent_id: int) -> None:
        """
        Delete all messages from an agent's conversation history.

        Args:
            agent_id (int): The ID of the agent whose messages to delete.
        """

        async with self.unit_of_work as uow:
            agent = await self.get_populated_agent(agent_id)
            if agent is None:
                return None

            agent.conversation_history.clear()

            await uow.agents.update(agent)

    async def update_agent_state(self, agent: Agent, state: State) -> Agent:
        """
        Update the state of an existing agent.

        Args:
            agent (Agent): The agent to update.
            state (State): The new state to assign to the agent.

        Returns:
            Agent: The updated agent.
        """

        async with self.unit_of_work as uow:
            agent.state = state
            return await uow.agents.update(agent)

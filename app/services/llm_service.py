import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.llm.models import ChainInput, ChainOutput
from app.llm.system_message import SYSTEM_MESSAGE_TEMPLATE
from app.models import Agent, AgentMessage, Player
from app.models.global_state import State

from .action_condition_service import ActionConditionService
from .base_service import BaseService

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


class LLMService(BaseService):
    async def query_agent(
        self, agent: Agent, query: str, caller: Player | Agent, global_state: State
    ) -> ChainOutput:
        """
        Queries an agent.

        Args:
            agent (Agent): The agent to query.
            query (str): The query to send to the agent.
            caller (Player | Agent): The caller of the agent.
            global_state (State): The current global state.

        Returns:
            ChainOutput: The response from the agent.
        """

        chain_input = ChainInput(
            query=str({"caller": caller.to_details(), "query": query}),
            instructions=agent.instructions or "",
            global_state=global_state,
            agent_internal_state=agent.internal_state,
            agent_external_state=agent.external_state,
            action_agents={
                action.name: action.triggered_agent.to_details()
                for action in agent.actions
                if action.triggered_agent is not None
            },
        )

        chain = await self._create_agent_chain(agent)
        return await chain.ainvoke(chain_input)

    async def _create_agent_chain(self, agent: Agent) -> Runnable[ChainInput, ChainOutput]:
        """
        Creates an LLM chain for the given agent.

        Args:
            agent (Agent): The agent to create the chain for.

        Returns:
            Runnable[ChainInput, ChainOutput]: The created chain.
        """

        async with self.unit_of_work as uow:
            chat_model = ChatOpenAI(model=OPENAI_MODEL)

            players, agents = await self._get_agent_conversation_history_callers(agent)

            prompt = ChatPromptTemplate(
                [
                    ("system", SYSTEM_MESSAGE_TEMPLATE),
                    *[
                        message
                        for agent_message in agent.conversation_history
                        for message in agent_message.to_llm_messages(
                            caller=self._find_message_caller(agent_message, players, agents)
                        )
                    ],
                    ("human", "{query}"),
                ]
            )

            available_actions = [
                action
                for action in agent.actions
                if await ActionConditionService(uow).evaluate_conditions(action)
            ]

            chat_model = chat_model.with_structured_output(
                agent.to_structured_output(available_actions), method="json_schema", strict=True
            )

            return prompt | chat_model

    def _find_message_caller(
        self, message: AgentMessage, players: list[Player], agents: list[Agent]
    ) -> Player | Agent | None:
        """
        Finds the caller of the given agent message from the provided lists of players and agents.

        Args:
            message (AgentMessage): The agent message to find the caller for.
            players (list[Player]): The list of players to search.
            agents (list[Agent]): The list of agents to search.

        Returns:
            Player | Agent | None: The caller of the message, or None if not found.
        """

        if message.caller_player_id:
            return next((p for p in players if p.id == message.caller_player_id), None)
        if message.caller_agent_id:
            return next((a for a in agents if a.id == message.caller_agent_id), None)
        return None

    async def _get_agent_conversation_history_callers(
        self, agent: Agent
    ) -> tuple[list[Player], list[Agent]]:
        """
        Gets the players and agents that have interacted with the given agent.

        Args:
            agent (Agent): The agent to get the conversation history callers for.

        Returns:
            tuple[list[Player], list[Agent]]:
                The players and agents that have interacted with the agent.
        """

        agent_ids = [
            message.caller_agent_id
            for message in agent.conversation_history
            if message.caller_agent_id is not None
        ]
        player_ids = [
            message.caller_player_id
            for message in agent.conversation_history
            if message.caller_player_id is not None
        ]

        async with self.unit_of_work as uow:
            agents = await uow.agents.find_all_by_ids(agent_ids)
            players = await uow.players.find_all_by_ids(player_ids)

        return players, agents

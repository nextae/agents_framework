from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from pydantic import BaseModel

from app.core.database import Session
from app.llm.models import ChainOutput
from app.models import Action, ActionConditionOperator, ActionParam, Agent, AgentMessage, Player
from app.models.action_condition import ActionCondition, ComparisonMethod, LogicalOperator
from app.models.action_param import ActionParamType
from app.models.agent_message import ActionResponseDict, QueryResponseDict
from app.services.agent import AgentService
from app.sockets.agent import query_agent
from app.sockets.models import ActionQueryResponse, AgentQueryRequest, AgentQueryResponse


@pytest.fixture(scope="module")
def query_id() -> Generator[UUID, None, None]:
    with patch("app.sockets.models.uuid4") as mock_uuid4:
        query_id = uuid4()
        mock_uuid4.return_value = query_id
        yield query_id


@pytest.fixture
def chat_model() -> Generator[MagicMock, None, None]:
    with patch("app.llm.chain.ChatOpenAI") as mock_chat_model:
        yield mock_chat_model.return_value.with_structured_output.return_value


@pytest.fixture
def sio() -> Generator[MagicMock, None, None]:
    with patch("app.sockets.agent.sio") as mock_sio:
        mock_sio.emit = AsyncMock()
        yield mock_sio


@pytest.fixture
def logger() -> Generator[MagicMock, None, None]:
    with patch("app.sockets.agent.logger") as mock_logger:
        yield mock_logger


@pytest.fixture
def build_actions_model():
    def _build(actions_dict: dict) -> MagicMock:
        actions_model = MagicMock(BaseModel)
        actions_model.model_dump.return_value = actions_dict
        return actions_model

    return _build


@pytest_asyncio.fixture
async def sample_player(insert) -> Player:
    player = Player(name="Player", description="Player description")
    return await insert(player)


@pytest_asyncio.fixture
async def sample_agent(insert) -> Agent:
    agent = Agent(
        name="Test Agent",
        description="Test agent description",
        instructions="You are a helpful test agent.",
    )
    return await insert(agent)


@pytest.fixture
def sample_action() -> Action:
    return Action(
        name="Sing",
        description="Sing a song",
        params=[
            ActionParam(
                name="song_name",
                description="Name of the song",
                type=ActionParamType.STRING,
                action_id=0,
            )
        ],
    )


@pytest_asyncio.fixture
async def agent_with_action(insert, sample_action: Action) -> Agent:
    agent = Agent(
        name="Singer",
        description="Singer agent that sings songs",
        instructions="You are a helpful assistant that sings songs.",
        actions=[sample_action],
    )
    return await insert(agent)


async def test_query_agent__success(
    sio,
    sid,
    query_id,
    chat_model,
    build_actions_model,
    sample_player,
    sample_action,
    insert,
    cleanup_db,
):
    # given
    message = AgentMessage(
        agent_id=0,
        caller_agent_id=0,
        caller_player_id=sample_player.id,
        query="hi, sing me a song",
        response=QueryResponseDict(
            response="Hello! Here's a song for you.",
            actions=[ActionResponseDict(name="Sing", params={"song_name": "Happy"})],
        ),
    )
    agent = Agent(
        name="Singer",
        description="Singer agent that sings songs",
        instructions="You are a helpful assistant that sings songs.",
        conversation_history=[message],
        actions=[sample_action],
    )
    agent = await insert(agent)

    request = AgentQueryRequest(
        agent_id=agent.id, player_id=sample_player.id, query="another song please"
    )

    chat_model.return_value = ChainOutput(
        response="Sure! Here's a song for you.",
        actions=build_actions_model({"Sing": {"song_name": "Twinkle Twinkle Little Star"}}),
    )

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": True}
    expected_agent_response = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent.id,
        response="Sure! Here's a song for you.",
        actions=[
            ActionQueryResponse(
                name="Sing",
                params={"song_name": "Twinkle Twinkle Little Star"},
                triggered_agent_id=None,
            )
        ],
    )
    sio.emit.assert_has_awaits(
        [
            call("agent_response", expected_agent_response.model_dump()),
            call("agent_response_end", {"query_id": str(query_id)}),
        ]
    )

    async with Session() as db:
        messages = await AgentService.get_agent_messages(agent.id, db)
        assert len(messages) == 2
        message = messages[1]
        assert message.caller_player_id == sample_player.id
        assert message.query == request.query
        assert message.response == expected_agent_response.to_message_response()
        assert message.agent_id == agent.id
        assert message.caller_agent_id is None


async def test_query_agent__trigger_agents__success(
    sio,
    sid,
    query_id,
    chat_model,
    logger,
    build_actions_model,
    insert,
    cleanup_db,
    sample_player,
    sample_action,
):
    # given
    agent_3 = Agent(
        name="Agent 3",
        description="Description for agent 3",
        instructions="Instructions for agent 3",
    )
    agent_3 = await insert(agent_3)

    action_2 = Action(
        name="Ask Agent 3",
        description="Ask Agent 3 to do something",
        params=[
            ActionParam(
                name="question",
                description="A question for Agent 3",
                type=ActionParamType.STRING,
                action_id=0,
            )
        ],
        triggered_agent_id=agent_3.id,
    )
    agent_2 = Agent(
        name="Agent 2",
        description="Description for agent 2",
        instructions="Instructions for agent 2",
        actions=[action_2],
    )
    agent_2 = await insert(agent_2)

    message = AgentMessage(
        agent_id=0,
        caller_agent_id=0,
        caller_player_id=sample_player.id,
        query="hi, sing me a song",
        response=QueryResponseDict(
            response="Hello! Here's a song for you.",
            actions=[ActionResponseDict(name="Sing", params={"song_name": "Happy"})],
        ),
    )
    sample_action.triggered_agent_id = agent_2.id
    agent = Agent(
        name="Singer",
        description="Singer agent that sings songs",
        instructions="You are a helpful assistant that sings songs.",
        conversation_history=[message],
        actions=[sample_action],
    )
    agent = await insert(agent)

    request = AgentQueryRequest(
        agent_id=agent.id, player_id=sample_player.id, query="another song please"
    )

    chat_model.side_effect = [
        ChainOutput(
            response="Sure! Here's a song for you.",
            actions=build_actions_model({"Sing": {"song_name": "Twinkle Twinkle Little Star"}}),
        ),
        ChainOutput(
            response="Agent 2 here, asking Agent 3.",
            actions=build_actions_model(
                {"Ask Agent 3": {"question": "What is the meaning of life?"}}
            ),
        ),
        ChainOutput(
            response="Agent 3 here, the meaning of life is 42.", actions=build_actions_model({})
        ),
    ]

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": True}
    expected_agent_response_1 = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent.id,
        response="Sure! Here's a song for you.",
        actions=[
            ActionQueryResponse(
                name="Sing",
                params={"song_name": "Twinkle Twinkle Little Star"},
                triggered_agent_id=agent_2.id,
            )
        ],
    )
    expected_agent_response_2 = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent_2.id,
        response="Agent 2 here, asking Agent 3.",
        actions=[
            ActionQueryResponse(
                name="Ask Agent 3",
                params={"question": "What is the meaning of life?"},
                triggered_agent_id=agent_3.id,
            )
        ],
    )
    expected_agent_response_3 = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent_3.id,
        response="Agent 3 here, the meaning of life is 42.",
        actions=[],
    )
    sio.emit.assert_has_awaits(
        [
            call("agent_response", expected_agent_response_1.model_dump()),
            call("agent_response", expected_agent_response_2.model_dump()),
            call("agent_response", expected_agent_response_3.model_dump()),
            call("agent_response_end", {"query_id": str(query_id)}),
        ]
    )
    logger.warning.assert_not_called()
    logger.debug.assert_has_calls(
        [
            call(f"Triggering agent {agent_2.name} from action {sample_action.name}"),
            call(f"Triggering agent {agent_3.name} from action {action_2.name}"),
        ]
    )

    async with Session() as db:
        messages = await AgentService.get_agent_messages(agent.id, db)
        assert len(messages) == 3
        message = messages[1]
        assert message.caller_player_id == sample_player.id
        assert message.query == request.query
        assert message.response == expected_agent_response_1.to_message_response()
        assert message.agent_id == agent.id
        assert message.caller_agent_id is None

        trigger_agent_2_message = messages[2]
        assert trigger_agent_2_message.caller_player_id is None
        assert trigger_agent_2_message.query == str({"song_name": "Twinkle Twinkle Little Star"})
        assert trigger_agent_2_message.response == expected_agent_response_2.to_message_response()
        assert trigger_agent_2_message.agent_id == agent_2.id
        assert trigger_agent_2_message.caller_agent_id == agent.id

        messages = await AgentService.get_agent_messages(agent_2.id, db)
        assert len(messages) == 2
        message = messages[0]
        assert message.caller_player_id is None
        assert message.query == str({"song_name": "Twinkle Twinkle Little Star"})
        assert message.response == expected_agent_response_2.to_message_response()
        assert message.agent_id == agent_2.id
        assert message.caller_agent_id == agent.id

        trigger_agent_3_message = messages[1]
        assert trigger_agent_3_message.caller_player_id is None
        assert trigger_agent_3_message.query == str({"question": "What is the meaning of life?"})
        assert trigger_agent_3_message.response == expected_agent_response_3.to_message_response()
        assert trigger_agent_3_message.agent_id == agent_3.id
        assert trigger_agent_3_message.caller_agent_id == agent_2.id

        messages = await AgentService.get_agent_messages(agent_3.id, db)
        assert len(messages) == 1
        message = messages[0]
        assert message.caller_player_id is None
        assert message.query == str({"question": "What is the meaning of life?"})
        assert message.response == expected_agent_response_3.to_message_response()
        assert message.agent_id == agent_3.id
        assert message.caller_agent_id == agent_2.id


async def test_query_agent__agent_not_found(sio, sid, sample_player, cleanup_db):
    # given
    request = AgentQueryRequest(agent_id=999, player_id=sample_player.id, query="hello")

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"error": f"Agent with id {request.agent_id} not found"}
    sio.emit.assert_not_awaited()


async def test_query_agent__player_not_found(sio, sid, sample_agent, cleanup_db):
    # given
    request = AgentQueryRequest(agent_id=sample_agent.id, player_id=999, query="hello")

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"error": f"Player with id {request.player_id} not found"}
    sio.emit.assert_not_awaited()


async def test_query_agent__condition_evaluation_error(sio, sid, sample_player, insert, cleanup_db):
    # given
    action = Action(
        name="Test Action",
        description="An action with a condition that will fail",
        params=[],
    )

    agent = Agent(name="Agent", state={"status": "active"}, actions=[action])
    agent = await insert(agent)

    condition_root = ActionConditionOperator(
        action_id=action.id,
        logical_operator=LogicalOperator.OR,
    )
    condition_root = await insert(condition_root)

    condition_root.root_id = condition_root.id
    condition_root = await insert(condition_root)

    condition = ActionCondition(
        parent_id=condition_root.id,
        root_id=condition_root.id,
        state_variable_name=f"agent-{agent.id}/status",
        comparison=ComparisonMethod.GREATER,
        expected_value="123",
    )
    await insert(condition)

    request = AgentQueryRequest(agent_id=agent.id, player_id=sample_player.id, query="hello")

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": False}
    sio.emit.assert_awaited_once_with(
        "agent_response_error",
        {
            "error": (
                "Condition evaluation error: Comparison 'GREATER' is not valid for values: "
                "state_var=active, expected_value=123"
            )
        },
    )


async def test_query_agent__internal_server_error(
    sio, sid, chat_model, sample_player, sample_agent, cleanup_db
):
    # given
    request = AgentQueryRequest(agent_id=sample_agent.id, player_id=sample_player.id, query="hello")

    chat_model.side_effect = Exception("LLM error")

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": False}
    sio.emit.assert_awaited_once_with(
        "agent_response_error", {"error": "Internal server error: LLM error"}
    )


async def test_query_agent__trigger_agents__condition_evaluation_error(
    sio,
    sid,
    query_id,
    chat_model,
    logger,
    build_actions_model,
    sample_player,
    sample_action,
    insert,
    cleanup_db,
):
    # given
    agent_3 = Agent(
        name="Agent 3",
        description="Description for agent 3",
        instructions="Instructions for agent 3",
    )
    agent_3 = await insert(agent_3)

    action_2 = Action(
        name="Ask Agent 3",
        description="Ask Agent 3 to do something",
        params=[
            ActionParam(
                name="question",
                description="A question for Agent 3",
                type=ActionParamType.STRING,
                action_id=0,
            )
        ],
        triggered_agent_id=agent_3.id,
    )
    agent_2 = Agent(
        name="Agent 2",
        description="Description for agent 2",
        instructions="Instructions for agent 2",
        state={"status": "active"},
        actions=[action_2],
    )
    agent_2 = await insert(agent_2)

    sample_action.triggered_agent_id = agent_2.id
    agent = Agent(
        name="Singer",
        description="Singer agent that sings songs",
        instructions="You are a helpful assistant that sings songs.",
        actions=[sample_action],
    )
    agent = await insert(agent)

    condition_root = ActionConditionOperator(
        action_id=action_2.id,
        logical_operator=LogicalOperator.OR,
    )
    condition_root = await insert(condition_root)

    condition_root.root_id = condition_root.id
    condition_root = await insert(condition_root)

    condition = ActionCondition(
        parent_id=condition_root.id,
        root_id=condition_root.id,
        state_variable_name=f"agent-{agent_2.id}/status",
        comparison=ComparisonMethod.GREATER,
        expected_value="123",
    )
    await insert(condition)

    request = AgentQueryRequest(
        agent_id=agent.id, player_id=sample_player.id, query="another song please"
    )

    chat_model.return_value = ChainOutput(
        response="Sure! Here's a song for you.",
        actions=build_actions_model({"Sing": {"song_name": "Twinkle Twinkle Little Star"}}),
    )

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": False}
    expected_agent_response = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent.id,
        response="Sure! Here's a song for you.",
        actions=[
            ActionQueryResponse(
                name="Sing",
                params={"song_name": "Twinkle Twinkle Little Star"},
                triggered_agent_id=agent_2.id,
            )
        ],
    )
    sio.emit.assert_has_awaits(
        [
            call("agent_response", expected_agent_response.model_dump()),
            call(
                "agent_response_error",
                {
                    "error": (
                        "Condition evaluation error: Comparison 'GREATER' is not valid for values: "
                        "state_var=active, expected_value=123"
                    )
                },
            ),
            call("agent_response_end", {"query_id": str(query_id)}),
        ]
    )
    logger.warning.assert_not_called()
    logger.debug.assert_called_once_with(
        f"Triggering agent {agent_2.name} from action {sample_action.name}"
    )


async def test_query_agent__trigger_agents__internal_server_error(
    sio,
    sid,
    query_id,
    chat_model,
    logger,
    build_actions_model,
    sample_player,
    agent_with_action,
    insert,
    cleanup_db,
):
    # given
    agent_2 = Agent(
        name="Agent 2",
        description="Description for agent 2",
        instructions="Instructions for agent 2",
    )
    agent_2 = await insert(agent_2)

    agent = agent_with_action
    agent.actions[0].triggered_agent_id = agent_2.id
    agent = await insert(agent)

    request = AgentQueryRequest(
        agent_id=agent.id, player_id=sample_player.id, query="another song please"
    )

    chat_model.side_effect = [
        ChainOutput(
            response="Sure! Here's a song for you.",
            actions=build_actions_model({"Sing": {"song_name": "Twinkle Twinkle Little Star"}}),
        ),
        Exception("LLM error"),
    ]

    # when
    result = await query_agent(sid, request.model_dump())

    # then
    assert result == {"success": False}
    expected_agent_response = AgentQueryResponse(
        query_id=query_id,
        agent_id=agent.id,
        response="Sure! Here's a song for you.",
        actions=[
            ActionQueryResponse(
                name="Sing",
                params={"song_name": "Twinkle Twinkle Little Star"},
                triggered_agent_id=agent_2.id,
            )
        ],
    )
    sio.emit.assert_has_awaits(
        [
            call("agent_response", expected_agent_response.model_dump()),
            call("agent_response_error", {"error": "Internal server error: LLM error"}),
            call("agent_response_end", {"query_id": str(query_id)}),
        ]
    )
    logger.warning.assert_not_called()
    logger.debug.assert_called_once_with(
        f"Triggering agent {agent_2.name} from action {agent_with_action.actions[0].name}"
    )


@pytest.mark.parametrize(
    "payload", [{}, {"agent_id": 1}, {"player_id": 1, "agent_id": 1, "query": True}]
)
async def test_query_agent__validation_error(sio, sid, payload):
    # when
    result = await query_agent(sid, payload)

    # then
    assert result == {"error": "Validation error."}
    sio.emit.assert_not_awaited()

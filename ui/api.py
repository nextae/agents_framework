import requests
import streamlit as st

from app.models.action import ActionResponse
from app.models.action_condition import ActionConditionResponse
from app.models.action_condition_operator import ActionConditionOperatorResponse
from app.models.action_param import ActionParamResponse
from app.models.agent import AgentResponse
from app.models.agent_message import AgentMessage
from app.models.player import PlayerResponse
from ui.models import Action, ActionParam, Agent, Condition, Operator, Player

BASE_URL = "http://localhost:8080/api/v1"


def error_toast(response: requests.Response) -> None:
    try:
        st.toast(
            "**Error:**\n" + str(response.json().get("detail")), icon=":material/error:"
        )
        print(response.json())
    except (AttributeError, ValueError):
        st.toast("**Error:**\n" + str(response.text), icon=":material/error:")


def fetch(method: str, endpoint: str, **kwargs) -> requests.Response | None:
    try:
        return requests.request(method, BASE_URL + endpoint, **kwargs)
    except requests.ConnectionError:
        st.toast(
            "**Error:**\nCould not connect to the server.",
            icon=":material/error:",
        )
        return None


# AGENTS


# @st.cache_data(ttl=60)
def get_agents() -> list[Agent]:
    print("Fetching agents")
    response = fetch("GET", "/agents")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return sorted(
        (
            Agent.from_response(AgentResponse.model_validate(agent))
            for agent in response.json()
        ),
        key=lambda agent: agent.id,
    )


def create_agent(agent_dict: dict) -> Agent | None:
    response = fetch("POST", "/agents", json=agent_dict)
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Agent.from_response(AgentResponse.model_validate(response.json()))


def update_agent(agent_dict: dict) -> Agent | None:
    response = fetch("PUT", f"/agents/{agent_dict['id']}", json=agent_dict)
    if response is None:
        return None

    if response.status_code != 200:
        error_toast(response)
        return None

    return Agent.from_response(AgentResponse.model_validate(response.json()))


def delete_agent(agent_id: int) -> bool:
    response = fetch("DELETE", f"/agents/{agent_id}")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


def get_agent_messages(agent_id: int) -> list[AgentMessage]:
    response = fetch("GET", f"/agents/{agent_id}/messages")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return [AgentMessage.model_validate(message) for message in response.json()]


def delete_agent_messages(agent_id: int) -> bool:
    response = fetch("DELETE", f"/agents/{agent_id}/messages")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


# ACTIONS


def assign_action(agent_id: int, action_id: int) -> bool:
    response = fetch(
        "POST",
        "/agents/assign_action",
        params={"agent_id": agent_id, "action_id": action_id},
    )
    if response is None:
        return False

    if response.status_code != 200:
        error_toast(response)
        return False

    return True


def remove_action(agent_id: int, action_id: int) -> bool:
    response = fetch(
        "POST",
        "/agents/remove_action",
        params={"agent_id": agent_id, "action_id": action_id},
    )
    if response is None:
        return False

    if response.status_code != 200:
        error_toast(response)
        return False

    return True


# @st.cache_data(ttl=60)
def get_actions() -> list[Action]:
    print("Fetching actions")
    response = fetch("GET", "/actions")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return sorted(
        (
            Action.from_response(ActionResponse.model_validate(action))
            for action in response.json()
        ),
        key=lambda action: action.id,
    )


def update_action(action_dict: dict) -> Action | None:
    response = fetch("PUT", f"/actions/{action_dict['id']}", json=action_dict)
    if response is None:
        return None

    if response.status_code != 200:
        error_toast(response)
        return None

    return Action.from_response(ActionResponse.model_validate(response.json()))


def create_action(action_dict: dict) -> Action | None:
    response = fetch("POST", "/actions", json=action_dict)
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Action.from_response(ActionResponse.model_validate(response.json()))


def delete_action(action_id: int) -> bool:
    response = fetch("DELETE", f"/actions/{action_id}")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


def evaluate_action_conditions(action_id: int) -> bool | None:
    response = fetch("POST", f"/actions/{action_id}/evaluate_conditions")
    if response is None:
        return None

    if response.status_code != 200:
        error_toast(response)
        return None

    return response.json()["result"]


# PARAMS


def create_action_param(param_dict: dict) -> ActionParam | None:
    response = fetch("POST", "/params", json=param_dict)
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return ActionParam.from_response(
        ActionParamResponse.model_validate(response.json())
    )


def update_action_param(param_dict: dict) -> ActionParam | None:
    response = fetch("PUT", f"/params/{param_dict['id']}", json=param_dict)
    if response is None:
        return None

    if response.status_code != 200:
        error_toast(response)
        return None

    return ActionParam.from_response(
        ActionParamResponse.model_validate(response.json())
    )


def delete_action_param(param_id: int) -> bool:
    response = fetch("DELETE", f"/params/{param_id}")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


# PLAYERS


# @st.cache_data(ttl=60)
def get_players() -> list[Player]:
    print("Fetching players")
    response = fetch("GET", "/players")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return sorted(
        (
            Player.from_response(PlayerResponse.model_validate(player))
            for player in response.json()
        ),
        key=lambda player: player.id,
    )


def create_player(player_dict: dict) -> Player | None:
    response = fetch("POST", "/players", json=player_dict)
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Player.from_response(PlayerResponse.model_validate(response.json()))


def update_player(player_dict: dict) -> Player | None:
    response = fetch("PUT", f"/players/{player_dict['id']}", json=player_dict)
    if response is None:
        return None

    if response.status_code != 200:
        error_toast(response)
        return None

    return Player.from_response(PlayerResponse.model_validate(response.json()))


def delete_player(player_id: int) -> bool:
    response = fetch("DELETE", f"/players/{player_id}")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


# CONDITIONS


def get_conditions() -> list[Condition]:
    print("Fetching conditions")
    response = fetch("GET", "/conditions/condition")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return [
        Condition.from_response(ActionConditionResponse.model_validate(condition))
        for condition in response.json()
    ]


def get_operators() -> list[Operator]:
    print("Fetching operators")
    response = fetch("GET", "/conditions/operator")
    if response is None:
        return []

    if response.status_code != 200:
        error_toast(response)
        return []

    return [
        Operator.from_response(ActionConditionOperatorResponse.model_validate(operator))
        for operator in response.json()
    ]


def create_condition_tree(tree_dict: dict) -> Operator | None:
    response = fetch("POST", "/conditions/tree", json=tree_dict)
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Operator.from_response(
        ActionConditionOperatorResponse.model_validate(response.json())
    )


def delete_condition_tree(root_id: int) -> bool:
    response = fetch("DELETE", f"/conditions/condition_tree/{root_id}")
    if response is None:
        return False

    if response.status_code != 204:
        error_toast(response)
        return False

    return True


def create_condition(condition: Condition) -> Condition | None:
    response = fetch("POST", "/conditions/condition", json=condition.model_dump())
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Condition.from_response(
        ActionConditionResponse.model_validate(response.json())
    )


def create_operator(operator: Operator) -> Operator | None:
    response = fetch("POST", "/conditions/operator", json=operator.model_dump())
    if response is None:
        return None

    if response.status_code != 201:
        error_toast(response)
        return None

    return Operator.from_response(
        ActionConditionOperatorResponse.model_validate(response.json())
    )

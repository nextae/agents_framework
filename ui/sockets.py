import os
from collections.abc import Generator
from typing import Any

import socketio
import streamlit as st
from socketio import exceptions

from app.sockets.models import AgentQueryResponse
from ui.utils import redirect_if_not_logged_in

API_HOST = os.getenv("API_HOST", "localhost")

redirect_if_not_logged_in()


@st.cache_resource
def get_socket_client(access_token: str) -> socketio.SimpleClient:
    """Creates a socket.io client and connects to the server."""

    client = socketio.SimpleClient()
    try:
        client.connect(
            f"http://{API_HOST}:8080",
            auth={"access_token": access_token},
            transports=["websocket"],
        )
    except exceptions.ConnectionError:
        st.toast("Failed to connect to the server.", icon=":material/error:")

    return client


client = get_socket_client(st.session_state.access_token)


def get_global_state() -> dict[str, Any]:
    return client.call("get_global_state")


def update_global_state(state: dict[str, Any]) -> dict[str, Any]:
    return client.call("update_global_state", {"state": state})


def get_agent_state(agent_id: int, internal: bool) -> dict[str, Any]:
    return client.call("get_agent_state", {"agent_id": agent_id, "internal": internal})


def get_combined_agent_state(agent_id: int) -> dict[str, Any]:
    return client.call("get_combined_agent_state", {"agent_id": agent_id})


def update_agent_state(agent_id: int, state: dict[str, Any], internal: bool) -> dict[str, Any]:
    return client.call(
        "update_agent_state", {"agent_id": agent_id, "state": state, "internal": internal}
    )


def query_agent(
    agent_id: int, player_id: int, query: str
) -> Generator[AgentQueryResponse, None, None]:
    client.emit(
        "query_agent",
        {
            "agent_id": agent_id,
            "player_id": player_id,
            "query": query,
        },
    )

    query_id = None
    while True:
        try:
            event, data = client.receive(timeout=20)
        except exceptions.TimeoutError:
            st.toast("Query timed out.", icon=":material/error:")
            return

        if event == "agent_response_end" and data["query_id"] == query_id:
            return
        elif event == "agent_response":
            response = AgentQueryResponse.model_validate(data)
            if query_id is None:
                query_id = str(response.query_id)
            elif query_id != str(response.query_id):
                continue

            yield response
        elif event == "agent_response_error":
            st.toast(data["error"], icon=":material/error:")
            return

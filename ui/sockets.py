from collections.abc import Generator
from typing import Any

import socketio
import streamlit as st
from socketio.exceptions import TimeoutError as SocketIOTimeoutError

from app.sockets.models import AgentQueryResponse


@st.cache_resource
def get_socket_client() -> socketio.SimpleClient:
    print("Creating socket client")
    client = socketio.SimpleClient()
    client.connect("http://localhost:8080", transports=["websocket"])
    return client


client = get_socket_client()


def get_global_state() -> dict[str, Any]:
    print("Getting global state")
    return client.call("get_global_state")


def update_global_state(state: dict[str, Any]) -> dict[str, Any]:
    return client.call("update_global_state", {"state": state})


def get_agent_state(agent_id: int) -> dict[str, Any]:
    print("Getting agent state")
    return client.call("get_agent_state", agent_id)


def update_agent_state(agent_id: int, state: dict[str, Any]) -> dict[str, Any]:
    return client.call("update_agent_state", {"agent_id": agent_id, "state": state})


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
            event, data = client.receive(timeout=10)
        except SocketIOTimeoutError:
            return

        if event == "agent_response_end" and data["query_id"] == query_id:
            return

        if event == "agent_response":
            response = AgentQueryResponse.model_validate(data)
            if query_id is None:
                query_id = str(response.query_id)
            elif query_id != str(response.query_id):
                continue

            yield response

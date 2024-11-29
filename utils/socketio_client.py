import json
from typing import Any

import socketio

client = socketio.Client()

PORT = 8080


def query_agent() -> None:
    agent_id = int(input("Enter the agent ID: "))
    query = input("Enter the query: ")

    client.emit(
        "query_agent",
        {"agent_id": agent_id, "query": query},
        callback=print_response_callback,
    )


def update_global_state() -> None:
    state = json.loads(input("Enter the state in JSON: "))

    client.emit(
        "update_global_state",
        {"state": state},
        callback=print_response_callback,
    )


def update_agent_state() -> None:
    agent_id = int(input("Enter the agent ID: "))
    state = json.loads(input("Enter the state in JSON: "))

    client.emit(
        "update_agent_state",
        {"agent_id": agent_id, "state": state},
        callback=print_response_callback,
    )


def print_response_callback(data: dict[str, Any]) -> None:
    print(data)


EVENTS = {
    "query_agent": query_agent,
    "update_global_state": update_global_state,
    "update_agent_state": update_agent_state,
}


@client.event
def connect():
    print("Connected to the server.")


if __name__ == "__main__":
    client.connect(f"http://localhost:{PORT}", transports=["websocket"])
    while True:
        event = input(f"Enter the event ({', '.join(EVENTS)}): ")
        if event == "/exit":
            break

        event_fn = EVENTS.get(event)
        if event_fn is None:
            print("Invalid event.")
            continue

        event_fn()
    client.disconnect()

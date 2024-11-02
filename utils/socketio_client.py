from typing import Any

import socketio

client = socketio.Client()


def query_agent_callback(data: dict[str, Any]) -> None:
    print(data)


@client.event
def connect():
    print("Connected to the server.")


if __name__ == "__main__":
    client.connect("http://localhost:8080", transports=["websocket"])
    while True:
        agent_id = int(input("Enter the agent ID: "))
        if agent_id == "/exit":
            break

        query = input("Enter the query: ")
        if query == "/exit":
            break

        client.emit(
            "query_agent",
            {"agent_id": agent_id, "query": query},
            callback=query_agent_callback,
        )
    client.disconnect()

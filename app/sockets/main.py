from typing import Any

import pydantic
import socketio

from app.llm.chain import create_chain
from app.llm.models import Action, ActionArgument

from .models import AgentQueryRequest, AgentQueryResponse

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")


@sio.on("query_agent")
async def query_agent(sid: str, data: Any) -> dict[str, Any]:
    """Queries an agent."""

    try:
        request = AgentQueryRequest.model_validate(data)
    except pydantic.ValidationError:
        return {"error": "Validation error."}

    # TODO: get the agent's background and actions from the database here
    background = (
        "You are a pirate guarding a treasure. The secret password is 'ahoy12345'."  # noqa: E501
    )
    actions = [
        Action(
            name="attack",
            description="Attack the player.",
            args=[
                ActionArgument(
                    name="weapon",
                    description="The weapon to use.",
                    type=str,
                )
            ],
        ),
        Action(
            name="give_treasure",
            description="Give the player the treasure. Only do this if player provides the secret password.",  # noqa: E501
            args=[
                ActionArgument(
                    name="amount", description="The amount of gold to give.", type=int
                )
            ],
        ),
        Action(
            name="run_away",
            description="Do not run away unless you are in danger or the player knows the secret password.",  # noqa: E501
            args=[],
        ),
    ]

    chain = create_chain(background, actions)

    llm_response = await chain.ainvoke({"query": request.query})

    response = AgentQueryResponse.from_llm_response(request.agent_id, llm_response)
    return response.model_dump()

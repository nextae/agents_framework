import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, create_model

from app.llm.models import Action

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


# TODO: make this a method of the Agent class e.g. agent.to_structured_output()
def create_structured_output(actions: list[Action]) -> type[BaseModel]:
    """Creates a Pydantic model for the structured output."""

    actions_model = create_model(
        "Actions",
        **{
            action.name: (
                action.to_structured_output() | None,
                Field(..., description=action.description),
            )
            for action in actions
        },
    )

    return create_model(
        "Response",
        response=(str, Field(..., description="The text response.")),
        actions=(actions_model, Field(..., description="The actions to take.")),
    )


# TODO: make a model for the input data or just use Agent here
def create_chain(
    system_message: str, actions: list[Action]
) -> Runnable[dict, BaseModel]:  # TODO: replace input with a model/TypedDict
    """Creates an LLM chain."""

    chat_model = ChatOpenAI(model=OPENAI_MODEL)
    prompt = ChatPromptTemplate(
        [
            ("system", system_message),
            # TODO: add message history
            ("human", "{query}"),
        ]
    )

    structured_output = create_structured_output(actions)

    chat_model = chat_model.with_structured_output(
        structured_output, method="json_schema", strict=True
    )

    return prompt | chat_model

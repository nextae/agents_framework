import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.llm.models import Action

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


# TODO: make a model for the input data
def create_chain(system_message: str, actions: list[Action]) -> Runnable:
    """Creates an LLM chain."""

    chat_model = ChatOpenAI(model=OPENAI_MODEL)
    prompt = ChatPromptTemplate(
        [
            ("system", system_message),
            # TODO: add message history
            ("human", "{query}"),
        ]
    )

    chat_model = chat_model.bind_tools([action.to_tool() for action in actions])

    return prompt | chat_model

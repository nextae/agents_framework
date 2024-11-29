import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.llm.models import ChainInput, ChainOutput
from app.llm.system_message import SYSTEM_MESSAGE_TEMPLATE

if TYPE_CHECKING:
    from app.models import Agent

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


def create_chain(agent: "Agent") -> Runnable[ChainInput, ChainOutput]:
    """Creates an LLM chain."""

    chat_model = ChatOpenAI(model=OPENAI_MODEL)
    prompt = ChatPromptTemplate(
        [
            ("system", SYSTEM_MESSAGE_TEMPLATE),
            # TODO: add message history
            ("human", "{query}"),
        ]
    )

    chat_model = chat_model.with_structured_output(
        agent.to_structured_output(), method="json_schema", strict=True
    )

    return prompt | chat_model

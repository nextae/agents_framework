import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession

from app.llm.models import ChainInput, ChainOutput
from app.llm.system_message import SYSTEM_MESSAGE_TEMPLATE

if TYPE_CHECKING:
    from app.models import Agent

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL")


async def create_chain(
    agent: "Agent", db: AsyncSession
) -> Runnable[ChainInput, ChainOutput]:
    """Creates an LLM chain."""

    chat_model = ChatOpenAI(model=OPENAI_MODEL)
    prompt = ChatPromptTemplate(
        [
            ("system", SYSTEM_MESSAGE_TEMPLATE),
            *[
                message
                for agent_message in agent.conversation_history
                for message in await agent_message.to_llm_messages(db)
            ],
            ("human", "{query}"),
        ]
    )

    chat_model = chat_model.with_structured_output(
        await agent.to_structured_output(db), method="json_schema", strict=True
    )

    return prompt | chat_model

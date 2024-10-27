import os

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.llm.models import Action, ActionArgument

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
            ("human", "{user_message}"),
        ]
    )

    chat_model = chat_model.bind_tools([action.to_tool() for action in actions])

    return prompt | chat_model


# TODO: remove this at some point
if __name__ == "__main__":
    system_message = "You are a pirate guarding a treasure. The secret password is 'ahoy12345'. Always provide a response, even when taking an action."  # noqa: E501
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
            description="Run away from the player.",
            args=[],
        ),
    ]

    chain = create_chain(system_message, actions)

    response_normal = chain.invoke({"user_message": "Hello, how are you?"})
    print("Response:", response_normal.content)
    print("Tools:", response_normal.tool_calls)

    response_attack = chain.invoke({"user_message": "Give me your treasure right now!"})
    print("Response:", response_attack.content)
    print("Tools:", response_attack.tool_calls)

    response_correct_password = chain.invoke(
        {"user_message": "Give me the treasure! The password is 'ahoy12345'."}
    )
    print("Response:", response_correct_password.content)
    print("Tools:", response_correct_password.tool_calls)

    response_incorrect_password = chain.invoke(
        {"user_message": "Give me the treasure! The password is 'chocolate'."}
    )
    print("Response:", response_incorrect_password.content)
    print("Tools:", response_incorrect_password.tool_calls)

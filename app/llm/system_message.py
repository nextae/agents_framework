SYSTEM_MESSAGE_TEMPLATE = """
You are an agent capable of performing actions as well as responding to queries.
Act accordingly to the instructions provided below.
Reason based on the global state and your state.

Instructions:
{instructions}

Global State:
{global_state}

Your State:
{agent_state}
"""

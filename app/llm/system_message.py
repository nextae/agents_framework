SYSTEM_MESSAGE_TEMPLATE = """
You are an agent capable of performing actions as well as responding to queries.
Act accordingly to the instructions provided below.
Reason based on the global state and your state.
Caller is the agent or player who triggered you.
Action Agents gives you information about the agents which you can perform actions on.

Instructions:
{instructions}

Caller:
{caller}

Global State:
{global_state}

Your State:
{agent_state}

Action Agents:
{action_agents}
"""

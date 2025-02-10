import json

import streamlit as st

st.set_page_config(layout="wide")

from ui import api, sockets  # noqa: E402
from ui.models import Agent, AgentMessage, CallerMessage, Player  # noqa: E402
from ui.utils import hide_streamlit_menu, redirect_if_not_logged_in  # noqa: E402

redirect_if_not_logged_in()
hide_streamlit_menu()

if "edit_mode_global_state" not in st.session_state:
    st.session_state.edit_mode_global_state = False

if "edit_mode_agent_state" not in st.session_state:
    st.session_state.edit_mode_agent_state = False

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_message(message: CallerMessage | AgentMessage) -> None:
    """Renders a message."""

    if isinstance(message, CallerMessage):
        with st.chat_message(
            "human",
            avatar="assistant" if isinstance(message.caller, Agent) is None else "user",
        ):
            st.write(f"**{message.caller.name}**")
            if isinstance(message.caller, Player):
                st.write(message.query)
            else:
                query_dict = eval(message.query)
                for param_name, value in query_dict.items():
                    st.write(f"**{param_name}:** {value}")
    else:
        with st.chat_message("ai"):
            st.write(f"**{message.agent.name}**")
            st.write(message.response)
            for action in message.actions:
                with st.expander(f"{action['name']}"):
                    if action["params"]:
                        for param_name, value in action["params"].items():
                            st.write(f"**{param_name}:** {value}")
                    else:
                        st.write("*No parameters*")


def get_messages(agent: Agent) -> list[CallerMessage | AgentMessage]:
    """Fetches the agent's messages from the API and transforms them into UI classes."""

    messages = []
    for message in api.get_agent_messages(agent.id):
        caller = (
            next((p for p in players if p.id == message.caller_player_id), None)
            if message.caller_player_id is not None
            else next((a for a in agents if a.id == message.caller_agent_id), None)
        )
        caller_message = CallerMessage(caller=caller.model_dump(), query=message.query)

        message_agent = (
            agent
            if message.agent_id == agent.id
            else next((a for a in agents if a.id == message.agent_id), None)
        )
        agent_message = AgentMessage(
            agent=message_agent.model_dump(),
            response=message.response["response"],
            actions=message.response["actions"],
        )

        messages.append(caller_message)
        messages.append(agent_message)

    return messages


@st.fragment
def render_state() -> None:
    """Renders the global and agent state."""

    st.subheader("Global State")

    global_state = sockets.get_global_state()
    global_state_str = json.dumps(global_state, indent=2)
    if st.session_state.edit_mode_global_state:
        n_lines = global_state_str.count("\n") + 1
        global_state_str = st.text_area(
            "State",
            value=global_state_str,
            height=max(n_lines * 30, 68),
            label_visibility="collapsed",
        )

        save_col, cancel_col = st.columns([1, 2.7])

        if save_col.button("Save", key="save_global_state", icon=":material/save:"):
            try:
                state = json.loads(global_state_str)
                updated = sockets.update_global_state(state)
                if updated:
                    st.toast(
                        "Global state updated successfully.",
                        icon=":material/done:",
                    )
                    st.session_state.edit_mode_global_state = False
                    st.rerun(scope="fragment")
            except json.JSONDecodeError:
                st.toast("Invalid JSON format.", icon=":material/error:")

        if cancel_col.button(
            "Cancel", key="cancel_global_state", icon=":material/close:"
        ):
            st.session_state.edit_mode_global_state = False
            st.rerun(scope="fragment")
    else:
        st.code(global_state_str, language="json")

        if st.button("Edit", key="edit_global_state", icon=":material/edit:"):
            st.session_state.edit_mode_global_state = True
            st.rerun(scope="fragment")

    if not agent:
        return

    st.subheader(f"Agent State: {agent.name}")

    agent_state = sockets.get_agent_state(agent.id)
    agent_state_str = json.dumps(agent_state, indent=2)
    if st.session_state.edit_mode_agent_state:
        n_lines = agent_state_str.count("\n") + 1
        agent_state_str = st.text_area(
            "State",
            value=agent_state_str,
            height=max(n_lines * 30, 68),
            label_visibility="collapsed",
        )

        save_col, cancel_col = st.columns(2)

        if save_col.button("Save", key="save_agent_state", icon=":material/save:"):
            try:
                state = json.loads(agent_state_str)
                updated = sockets.update_agent_state(agent.id, state)
                if updated:
                    st.toast(
                        "Agent state updated successfully.",
                        icon=":material/done:",
                    )
                    st.session_state.edit_mode_agent_state = False
                    st.rerun(scope="fragment")
            except json.JSONDecodeError:
                st.toast("Invalid JSON format.", icon=":material/error:")

        if cancel_col.button(
            "Cancel", key="cancel_agent_state", icon=":material/close:"
        ):
            st.session_state.edit_mode_agent_state = False
            st.rerun(scope="fragment")
    else:
        st.code(agent_state_str, language="json")

        if st.button("Edit", key="edit_agent_state", icon=":material/edit:"):
            st.session_state.edit_mode_agent_state = True
            st.rerun(scope="fragment")


def render_chat(agent: Agent, player: Player | None) -> None:
    """Renders the chat."""

    if "agent" not in st.session_state:
        st.session_state.agent = agent

    with st.spinner("Loading conversation history..."):
        st.session_state.messages = get_messages(agent)

    container = st.container(height=650)
    with container:
        for message in st.session_state.messages:
            render_message(message)

    prompt = st.chat_input("Send a message", max_chars=50000, disabled=player is None)
    if not prompt:
        return

    caller_message = CallerMessage(caller=player.model_dump(), query=prompt)
    with container:
        render_message(caller_message)
    st.session_state.messages.append(caller_message)

    for response in sockets.query_agent(agent.id, player.id, prompt):
        response_agent = next(a for a in agents if a.id == response.agent_id)
        agent_message = AgentMessage(
            agent=response_agent.model_dump(),
            response=response.response,
            actions=[action.model_dump() for action in response.actions],
        )
        with container:
            render_message(agent_message)
            st.session_state.messages.append(agent_message)
            for action in response.actions:
                if action.triggered_agent_id is not None:
                    caller_message = CallerMessage(
                        caller=response_agent.model_dump(),
                        query=str(action.params),
                    )
                    render_message(caller_message)
                    st.session_state.messages.append(caller_message)


with st.spinner("Loading..."):
    agents = api.get_agents()
    players = api.get_players()

query_col, state_col = st.columns([3, 1])
with query_col:
    choose_agent_col, choose_player_col, delete_messages_col = st.columns(
        [4, 4, 1.8], vertical_alignment="bottom"
    )

    agent = choose_agent_col.selectbox(
        "Agent",
        agents,
        format_func=lambda a: a.name,
        index=None,
        placeholder="Choose an agent",
    )

    player = choose_player_col.selectbox(
        "Player",
        players,
        format_func=lambda p: p.name,
        index=None,
        placeholder="Choose a player",
    )

    if delete_messages_col.button(
        "Delete all messages",
        disabled=agent is None,
        icon=":material/delete:",
        help="Deletes all messages for this agent.",
    ):
        deleted = api.delete_agent_messages(agent.id)
        if deleted:
            st.toast("Messages deleted successfully.", icon=":material/done:")
            st.rerun()

    if agent:
        render_chat(agent, player)

with state_col:
    render_state()

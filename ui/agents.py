import streamlit as st
import streamlit_pydantic as sp

from ui import api
from ui.models import Action, Agent
from ui.utils import hide_streamlit_menu

st.set_page_config(layout="wide")

hide_streamlit_menu()


def save_agent(
    agent: Agent, updated_agent: dict, selected_actions: list[Action]
) -> None:
    """Saves the updated agent and its actions."""

    updated_agent = api.update_agent(updated_agent)
    if not updated_agent:
        return

    action_ids_to_assign = [
        action.id
        for action in actions
        if action in selected_actions and action.id not in agent.actions_ids
    ]
    action_ids_to_remove = [
        action.id
        for action in actions
        if action not in selected_actions and action.id in agent.actions_ids
    ]

    assigned_actions = [
        api.assign_action(agent.id, action_id) for action_id in action_ids_to_assign
    ]
    removed_actions = [
        api.remove_action(agent.id, action_id) for action_id in action_ids_to_remove
    ]

    if all(assigned_actions) and all(removed_actions):
        api.get_agents.clear()
        st.toast("Agent saved successfully.", icon=":material/done:")


@st.dialog("Add agent")
def add_agent_dialog():
    """Renders a dialog to create a new agent."""

    agent_name = st.text_input("Name", help="The name of the agent.")
    agent_description = st.text_area(
        "Description",
        help=(
            "Description of the agent.\n\n"
            "This is what other agents will know about this agent."
        ),
    )
    agent_instructions = st.text_area(
        "Instructions",
        help=(
            "Instructions for the agent.\n\n"
            "Describe the agent's behavior and how it should respond."
        ),
    )

    if st.button("Submit", disabled=not agent_name):
        agent_dict = {
            "name": agent_name,
            "description": agent_description,
            "instructions": agent_instructions,
        }
        created_agent = api.create_agent(agent_dict)
        if created_agent:
            api.get_agents.clear()
            st.toast("Agent added successfully.", icon=":material/done:")
            st.rerun()


def actions_changed(agent: Agent, selected_actions: list[Action]) -> bool:
    """Checks if the actions assigned to the agent have changed."""

    return sorted(action.id for action in selected_actions) != sorted(
        action.id for action in actions if action.id in agent.actions_ids
    )


def render_agent(agent: Agent) -> None:
    """Renders an agent's details and actions."""

    with st.expander(agent.name):
        form_model = agent.to_form_model()
        updated_agent = sp.pydantic_input(f"agent_{agent.id}", form_model)
        selected_actions = st.multiselect(
            "Actions",
            actions,
            format_func=lambda action: action.name,
            default=[action for action in actions if action.id in agent.actions_ids],
            help="The actions that this agent can perform",
            placeholder="Choose actions",
            key=f"actions_{agent.id}",
        )

        save_col, delete_col = st.columns([1, 13])

        save_button = save_col.button(
            "Save",
            disabled=(
                (
                    updated_agent == form_model.model_dump()
                    and not actions_changed(agent, selected_actions)
                )
                or not updated_agent["name"]
            ),
            key=f"save_{agent.id}",
            icon=":material/save:",
            type="primary",
        )
        if save_button:
            save_agent(agent, updated_agent, selected_actions)

        delete_button = delete_col.button(
            "Delete", key=f"delete_{agent.id}", icon=":material/delete:"
        )
        if delete_button:
            deleted = api.delete_agent(agent.id)
            if deleted:
                api.get_agents.clear()
                st.toast("Agent deleted successfully.", icon=":material/done:")
                st.rerun()


st.header("Agents")

with st.spinner("Loading..."):
    actions = api.get_actions()
    agents = api.get_agents()
    for agent in agents:
        render_agent(agent)

if st.button("Add agent", icon=":material/add:"):
    add_agent_dialog()

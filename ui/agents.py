import streamlit as st
import streamlit_pydantic as sp

from ui import api
from ui.models import Action, Agent

st.set_page_config(layout="wide")

st.header("Agents")


def save_agent(
    agent: Agent, updated_agent: dict, selected_actions: list[Action]
) -> None:
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
        # api.get_agents.clear()
        st.toast("Agent saved successfully.", icon=":material/done:")


@st.dialog("Add agent")
def add_agent_dialog():
    agent_name = st.text_input("Name", help="The name of the agent.")
    agent_description = st.text_area("Description", help="A description of the agent.")
    agent_instructions = st.text_area(
        "Instructions", help="Instructions for the agent."
    )

    if st.button("Submit"):
        agent_dict = {
            "name": agent_name,
            "description": agent_description,
            "instructions": agent_instructions,
        }
        created_agent = api.create_agent(agent_dict)
        if created_agent:
            # api.get_agents.clear()
            st.toast("Agent added successfully.", icon=":material/done:")
            st.rerun()


def actions_changed(agent: Agent, selected_actions: list[Action]) -> bool:
    return sorted([action.id for action in selected_actions]) != sorted(
        [action.id for action in actions if action.id in agent.actions_ids]
    )


def render_agent(agent: Agent) -> None:
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

        with save_col:
            save_button = st.button(
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

        with delete_col:
            delete_button = st.button(
                "Delete", key=f"delete_{agent.id}", icon=":material/delete:"
            )
            if delete_button:
                deleted = api.delete_agent(agent.id)
                if deleted:
                    # api.get_agents.clear()
                    st.toast("Agent deleted successfully.", icon=":material/done:")
                    st.rerun()


with st.spinner("Loading..."):
    actions = api.get_actions()
    agents = api.get_agents()
    for agent in agents:
        render_agent(agent)


if st.button("Add agent", icon=":material/add:"):
    add_agent_dialog()

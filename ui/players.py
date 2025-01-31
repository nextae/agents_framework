import streamlit as st
import streamlit_pydantic as sp

from ui import api
from ui.models import Player

st.set_page_config(layout="wide")

st.header("Players")


@st.dialog("Add player")
def add_player_dialog():
    player_name = st.text_input("Name", help="The name of the player.")
    player_description = st.text_area(
        "Description", help="A description of the player."
    )

    if st.button("Submit", disabled=not player_name):
        player_dict = {"name": player_name, "description": player_description}
        created_player = api.create_player(player_dict)
        if created_player:
            # api.get_agents.clear()
            st.toast("Player added successfully.", icon=":material/done:")
            st.rerun()


def render_player(player: Player) -> None:
    with st.expander(player.name):
        updated_player = sp.pydantic_input(f"player_{player.id}", player)

        save_col, delete_col = st.columns([1, 13])

        with save_col:
            save_button = st.button(
                "Save",
                key=f"save_{player.id}",
                icon=":material/save:",
                type="primary",
                disabled=(
                    updated_player == player.model_dump() or not updated_player["name"]
                ),
            )
            if save_button:
                updated_player = api.update_player(updated_player)
                if updated_player:
                    # api.get_agents.clear()
                    st.toast("Player saved successfully.", icon=":material/done:")

        with delete_col:
            delete_button = st.button(
                "Delete", key=f"delete_{player.id}", icon=":material/delete:"
            )
            if delete_button:
                deleted = api.delete_player(player.id)
                if deleted:
                    # api.get_agents.clear()
                    st.toast("Player deleted successfully.", icon=":material/done:")
                    st.rerun()


with st.spinner("Loading..."):
    players = api.get_players()
    for player in players:
        render_player(player)


if st.button("Add player", icon=":material/add:"):
    add_player_dialog()

import streamlit as st
import streamlit_pydantic as sp

from ui import api
from ui.models import Player
from ui.utils import hide_streamlit_menu

st.set_page_config(layout="wide")

hide_streamlit_menu()


@st.dialog("Add player")
def add_player_dialog():
    """Renders a dialog to create a new player."""

    player_name = st.text_input("Name", help="The name of the player.")
    player_description = st.text_area(
        "Description",
        help=(
            "Description of the player.\n\n"
            "This is what agents will know about this player."
        ),
    )

    if st.button("Submit", disabled=not player_name):
        player_dict = {"name": player_name, "description": player_description}
        created_player = api.create_player(player_dict)
        if created_player:
            api.get_players.clear()
            st.toast("Player added successfully.", icon=":material/done:")
            st.rerun()


def render_player(player: Player) -> None:
    """Renders a player's details."""

    with st.expander(player.name):
        updated_player = sp.pydantic_input(f"player_{player.id}", player)

        save_col, delete_col = st.columns([1, 13])

        save_button = save_col.button(
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
                api.get_players.clear()
                st.toast("Player saved successfully.", icon=":material/done:")

        delete_button = delete_col.button(
            "Delete", key=f"delete_{player.id}", icon=":material/delete:"
        )
        if delete_button:
            deleted = api.delete_player(player.id)
            if deleted:
                api.get_players.clear()
                st.toast("Player deleted successfully.", icon=":material/done:")
                st.rerun()


st.header("Players")

with st.spinner("Loading..."):
    players = api.get_players()
    for player in players:
        render_player(player)


if st.button("Add player", icon=":material/add:"):
    add_player_dialog()

import streamlit as st

st.set_page_config(layout="centered")

from ui import api  # noqa: E402
from ui.utils import hide_streamlit_menu  # noqa: E402

hide_streamlit_menu()

if "session_expired" in st.session_state:
    st.toast("**Session expired!**\nPlease log in again.", icon=":material/warning:")
    del st.session_state.session_expired


with st.container(border=True):
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login", disabled=not (username and password)):
        logged_in = api.login(username, password)

        if logged_in:
            st.success("Logged in successfully!")
            st.switch_page("agents.py")
        else:
            st.error("Incorrect username or password!")

import streamlit as st

if "access_token" not in st.session_state:
    st.session_state.access_token = None

logged_in = st.session_state.access_token is not None

agents = st.Page(
    "agents.py", default=logged_in, title="Agents", icon=":material/groups:"
)
actions = st.Page("actions.py", title="Actions", icon=":material/assignment:")
players = st.Page("players.py", title="Players", icon=":material/people:")
playground = st.Page("playground.py", title="Playground", icon=":material/insights:")
login = st.Page("login.py", default=True, title="Login", icon=":material/lock:")

pages = [agents, actions, players, playground]
if not logged_in:
    pages.append(login)

pg = st.navigation(pages, position="hidden" if not logged_in else "sidebar")

pg.run()

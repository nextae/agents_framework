import streamlit as st

agents = st.Page("agents.py", title="Agents", default=True, icon=":material/groups:")
actions = st.Page("actions.py", title="Actions", icon=":material/assignment:")
players = st.Page("players.py", title="Players", icon=":material/people:")
playground = st.Page("playground.py", title="Playground", icon=":material/insights:")

pg = st.navigation([agents, actions, players, playground])
pg.run()

import streamlit as st


def hide_streamlit_menu() -> None:
    st.markdown(
        """
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            #MainMenu {visibility: hidden;}
            .stAppToolbar {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
        </style>
    """,
        unsafe_allow_html=True,
    )


def set_horizontal_buttons_width() -> None:
    st.markdown(
        """
        <style>
            div[data-testid="stColumn"] {
                width: fit-content !important;
                flex: unset;
            }
            div[data-testid="stColumn"] * {
                width: fit-content !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def redirect_if_not_logged_in() -> None:
    if st.session_state.access_token is None:
        st.switch_page("login.py")

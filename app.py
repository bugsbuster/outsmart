"""
Entry point for the Outsmart Arena LLM Battle
Initialize logging, env variables and styling as needed
Check if an Arena is in the session, and if not, create a new one using Arena.default()
Delegate to a Display object to manage the drawing of the UI components

To see it in action, run:
python -m streamlit run app.py
"""

from dotenv import load_dotenv
import logging
from game.arenas import Arena
from interfaces.llms import LLM
import streamlit as st
from util.setup import setup_logger, STYLE
from views.displays import Display
from views.setup import display_setup

root = logging.getLogger()
if "root" not in st.session_state:
    st.session_state.root = root
    setup_logger(root)

load_dotenv(override=True)

st.set_page_config(
    layout="wide",
    page_title="Outsmart",
    menu_items={
        "About": "Outsmart is an LLM arena that pits LLMs against each other in a battle of negotiation. More at https://edwarddonner.com/2024/08/06/outsmart/"
    },
    page_icon="🧠",
    initial_sidebar_state="collapsed",
)
st.markdown(STYLE, unsafe_allow_html=True)

if "arena" not in st.session_state:
    result = display_setup()
    if result is None:
        st.stop()
    chosen_models, save_results = result
    st.session_state.arena = Arena.with_models(chosen_models, save_results=save_results)
    st.session_state.auto_move = False
    st.session_state.do_move = False
    st.rerun()

if "auto_move" not in st.session_state:
    st.session_state.auto_move = False
    st.session_state.do_move = False
arena = st.session_state.arena

Display(arena).display_page()

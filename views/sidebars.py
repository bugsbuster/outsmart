import os
import streamlit as st
from game.arenas import Arena
from models.games import Game


def display_ranks():
    st.markdown(
        "<span style='font-size:13px;'>The table is sorted initially by Win %. "
        "This only shows recent versions of models. "
        "The skill ratings use the TrueSkill methodology,"
        " an ELO-style system for multi-player games.</span>",
        unsafe_allow_html=True,
    )
    column_config = {
        "LLM": st.column_config.TextColumn(width="small"),
        "Win %": st.column_config.NumberColumn(format="%.1f"),
        "Skill": st.column_config.NumberColumn(format="%.1f"),
    }
    st.dataframe(data=Arena.rankings(), hide_index=True, column_config=column_config)


def display_latest():
    st.write("Latest games")
    column_config = {
        "When": st.column_config.DatetimeColumn(width="small"),
        "Winner(s)": st.column_config.TextColumn(width="medium"),
    }
    st.dataframe(data=Arena.latest(), hide_index=True, column_config=column_config)


def display_sidebar():
    with st.sidebar:
        st.markdown("### Outsmart Leaderboard")
        mongo_uri = os.getenv("MONGO_URI")

        if not mongo_uri:
            st.warning(
                "MONGO_URI is not set — leaderboard unavailable.  \n"
                "Add it to your environment variables to enable rankings."
            )
            return

        try:
            count = Game.count()
        except Exception as e:
            st.error(
                f"MONGO_URI is set but the database connection failed.  \n"
                f"**Error:** `{e}`  \n\n"
                "Check that the URI is correct and the cluster is reachable."
            )
            return

        st.write(f"There have been {count:,} games recorded.")
        if st.button("Calculate Rankings"):
            try:
                display_ranks()
                display_latest()
            except Exception as e:
                st.error(f"Failed to load rankings: `{e}`")

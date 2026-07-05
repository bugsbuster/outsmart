import logging
import re
from game.arenas import Arena
import streamlit as st
from views.headers import display_headers
from views.sidebars import display_sidebar
from util.setup import PLAYER_COLORS_ST


def _strip_think(text: str) -> str:
    """Remove <think>...</think> blocks that some models include in their output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class Display:
    """
    The User Interface for an Arena using streamlit
    """

    arena: Arena
    color_map: dict  # player name → Streamlit color name

    def __init__(self, arena: Arena):
        self.arena = arena
        self.progress_container = None
        self.color_map = {
            p.name: PLAYER_COLORS_ST[i % len(PLAYER_COLORS_ST)]
            for i, p in enumerate(arena.players)
        }

    def _colored(self, name: str) -> str:
        """Return Streamlit colored markup for a player name."""
        color = self.color_map.get(name, "gray")
        return f":{color}[{name}]"

    def display_record(self, rec) -> None:
        """
        Describe the most recent Turn Record on the UI.
        Shows strategy (with think-tags stripped), give/take, alliances, and received messages.
        """
        if rec.is_invalid_move:
            st.write("Illegal last move")
            return

        strategy = _strip_think(rec.move.strategy)
        text = f"Strategy: {strategy}  \n\n"
        text += f"- Gave to {self._colored(rec.move.give)}\n"
        text += f"- Took from {self._colored(rec.move.take)}\n"
        if rec.alliances_with:
            allies = ", ".join(self._colored(a) for a in rec.alliances_with)
            text += f"- :green[Alliance with] {allies}\n"
        if rec.alliances_against:
            attackers = ", ".join(self._colored(a) for a in rec.alliances_against)
            text += f"- :red[Ganged up on by] {attackers}"
        st.write(text)

        if rec.messages:
            st.markdown("**Messages received:**")
            for sender, msg in rec.messages.items():
                st.markdown(f"{self._colored(sender)}: *{msg}*")

    def display_player_title(self, each) -> None:
        """
        Show the player's title using their assigned identity color.
        Adds a trophy or skull indicator at game end without changing the color.
        """
        color = self.color_map.get(each.name, "blue")
        if each.is_dead:
            st.header(f":{color}[💀 {each.name}]")
        elif each.is_winner:
            st.header(f":{color}[🏆 {each.name}]")
        else:
            st.header(f":{color}[{each.name}]")

    def display_player(self, each) -> None:
        """
        Show the player, including title, coins, expander and latest turn
        """
        self.display_player_title(each)
        st.write(each.llm.model_name)
        records = each.records
        st.metric("Coins", each.coins, each.coins - each.prior_coins)
        with st.expander("Inner thoughts", expanded=False):
            st.markdown(
                f'<p class="small-font">{each.report()}</p>', unsafe_allow_html=True
            )
        if len(records) > 0:
            self.display_record(records[-1])

    def do_turn(self) -> None:
        """
        Callback to run a turn, either triggered from the Run Turn button, or automatically if a game is on auto
        """
        logging.info("Kicking off turn")
        with self.progress_container.container():
            bar = st.progress(0.0, text="Kicking off turn")
        self.arena.do_turn(bar.progress)
        bar.empty()

    def do_auto_turn(self) -> None:
        """
        Callback to run a turn on automatic mode, after the Run Game button has been pressed
        """
        st.session_state.auto_move = False
        self.do_turn()
        if not self.arena.is_game_over:
            st.session_state.auto_move = True

    def display_page(self) -> None:
        """
        Show the full UI, including columns for each player, and handle auto run if the Run Game button was pressed
        """
        display_sidebar()
        display_headers(self.arena, self.do_turn, self.do_auto_turn)
        self.progress_container = st.empty()
        player_columns = st.columns(len(self.arena.players))

        for index, player_column in enumerate(player_columns):
            player = self.arena.players[index]
            with player_column:
                inner = st.empty()
                with inner.container():
                    self.display_player(player)

        if st.session_state.auto_move:
            self.do_auto_turn()
            st.rerun()

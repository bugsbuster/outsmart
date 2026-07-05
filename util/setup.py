import logging
import sys

# One color per player slot — used consistently in chart, titles, and name references
PLAYER_COLORS_HEX = ["#1f77b4", "#ff7f0e", "#9467bd", "#7f7f7f"]
PLAYER_COLORS_ST = ["blue", "orange", "violet", "gray"]


def setup_logger(root) -> None:
    """
    Set up consistent logging
    """
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %z",
    )
    handler.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(handler)


STYLE = """
<style>
.small-font {
    font-size:12px !important;
}
</style>
"""

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
python -m streamlit run app.py
```

Requires a `.env` file in the project root:
```
OPENAI_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
GROK_API_KEY=xxxx
ARENA=random          # optional: "random" picks 4 random models; omit for the default cheap set
MONGO_URI=xxxx        # optional: enables leaderboard persistence
```

Python 3.11 is required. Use `black` for formatting.

## Architecture

Outsmart is a Streamlit app where 4 LLMs compete in a negotiation game. Each player starts with 12 coins; each turn they send private messages to opponents and choose to give 1 coin and take 1 coin. An alliance bonus applies when 2 players mutually give each other coins and both take from the same third player. The game ends after 10 turns or when a player hits 0 coins.

### Execution flow

`app.py` bootstraps Streamlit and stores an `Arena` in `st.session_state`. On each button press it calls `Arena.do_turn()`, which delegates to `Referee`. The `Referee` calls each `Player.make_move()` in parallel via `ThreadPoolExecutor`, parses the returned JSON into a `Move`, then applies coin changes and resolves alliances.

### Key layers

- **`game/`** — core game logic
  - `Arena` — creates/manages players, drives turns, handles game-over, saves results to MongoDB, builds leaderboard DataFrames.
  - `Player` — wraps an `LLM`, constructs prompts, stores per-player turn history (`records: List[TurnRecord]`).
  - `Referee` — orchestrates a single turn: parallel LLM calls → parse JSON → apply giving/taking/alliance rules.

- **`interfaces/llms.py`** — provider abstraction. `LLM` is an abstract base class; each concrete subclass (e.g. `GPT`, `Claude`, `Gemini`, `Grok`, `GroqAPI`) declares a `model_names` list and implements `setup_client()` and `send()`. `LLM.for_model_name()` auto-discovers all subclasses via `__subclasses__()` to return the right instance — **adding a new provider means only adding a subclass here**.

- **`models/`** — data structures
  - `Move` (Pydantic) — parsed LLM response: `strategy`, `give`, `take`, `messages`. Field aliases match the JSON keys the LLM must emit.
  - `TurnRecord` — per-player per-turn outcome: givers, takers, alliances, received messages. Its `__repr__` serialises to text fed back into subsequent user prompts.
  - `Result` / `Game` (Pydantic + MongoDB) — game persistence and leaderboard computation using the TrueSkill rating system.

- **`prompting/`** — prompt construction (pure functions, no game state)
  - `system.py` — static game rules + JSON response schema sent as the system prompt.
  - `user.py` — per-turn prompt that includes the full turn-by-turn history (via `TurnRecord.__repr__`) and current coin counts.

- **`views/`** — Streamlit UI only; no game logic
  - `Display` — renders player columns, coin metrics, inner thoughts expanders, progress bar during LLM calls.
  - `display_sidebar()` — leaderboard and recent games (only active when `MONGO_URI` is set).
  - `display_headers()` — title, "Run Turn" and "Run Game" buttons.

### LLM response contract

Each LLM must return a JSON object with exactly these keys (matched by Pydantic field aliases in `Move`):
```json
{
  "secret strategy": "...",
  "give coin to": "<player name>",
  "take coin from": "<player name>",
  "private messages": { "<name>": "..." }
}
```
`Referee.parse_response()` extracts the first `{…}` block, so preamble text is tolerated. Invalid or illegal JSON causes the move to be skipped (`is_invalid_move = True`).

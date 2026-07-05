import os
from typing import List
import streamlit as st
from interfaces.llms import LLM


def _model_input(provider_class, player_index: int) -> str:
    """
    Render the model selection widget for a given provider.
    Returns the full model name (with prefix for Ollama/OpenRouter).
    """
    key = f"model_{player_index}"

    if provider_class.provider_name == "Ollama (local)":
        search = st.text_input(
            "Filter models",
            placeholder="type to filter...",
            key=f"search_{player_index}",
            label_visibility="collapsed",
        )
        filtered = [
            m for m in provider_class.model_names
            if search.lower() in m.lower()
        ] if search else provider_class.model_names
        if not filtered:
            st.caption("No models match")
            return ""
        return st.selectbox(
            "Model",
            options=filtered,
            key=key,
            label_visibility="collapsed",
        )

    if provider_class.supports_custom_input:
        raw = st.text_input(
            "Model",
            placeholder="e.g. meta-llama/llama-3.1-8b-instruct",
            key=key,
            label_visibility="collapsed",
        )
        prefix = provider_class.model_prefixes[0] if provider_class.model_prefixes else ""
        return prefix + raw.strip() if raw.strip() else ""

    # Non-discovery provider: text input pre-filled with first known model
    default = provider_class.model_names[0] if provider_class.model_names else ""
    return st.text_input(
        "Model",
        value=default,
        key=key,
        label_visibility="collapsed",
    )


def display_setup() -> tuple[List[str], bool] | None:
    """
    Show the model selection screen.
    Returns (model_names, save_results) when the user clicks Start, otherwise None.
    """
    providers = LLM.available_providers()

    if len(providers) < 1:
        missing = LLM.missing_keys()
        st.error(
            "No LLM providers are configured.\n\n"
            "Set at least one of these environment variables:\n\n"
            + "\n".join(f"- `{k}`" for k in missing)
        )
        st.stop()

    st.markdown("<h1 style='text-align: center;'>Outsmart</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center;'>A battle of diplomacy and deviousness between LLMs</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    provider_names = [p.provider_name for p in providers]
    provider_map = {p.provider_name: p for p in providers}

    player_count = st.select_slider(
        "Number of players",
        options=[3, 4],
        value=4,
    )

    player_names = ["Alex", "Blake", "Charlie", "Drew"]
    cols = st.columns(player_count)
    selected = []

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{player_names[i]}**")
            default_provider = provider_names[i % len(provider_names)]
            chosen_provider_name = st.selectbox(
                "Provider",
                options=provider_names,
                index=provider_names.index(default_provider),
                key=f"provider_{i}",
                label_visibility="collapsed",
            )
            provider_class = provider_map[chosen_provider_name]
            model = _model_input(provider_class, i)
            selected.append(model)

    st.write("")

    save_results = True
    if os.getenv("MONGO_URI"):
        save_results = st.checkbox("Save game results to database", value=False)

    incomplete = [player_names[i] for i, m in enumerate(selected) if not m]
    if incomplete:
        st.caption(f"Enter a model for: {', '.join(incomplete)}")

    if st.button("Start Game", type="primary", disabled=bool(incomplete)):
        return selected, save_results

    return None

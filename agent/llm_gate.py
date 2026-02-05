def should_use_llm(strategy: str, agent_state: dict) -> bool:
    turns = agent_state.get("turns", 0)
    llm_calls = agent_state.get("llm_calls", 0)

    # Absolute safety cap per session
    if llm_calls >= 5:
        return False

    # Only allow LLM for high-value strategies
    if strategy in ["extract_payment", "extract_identity"]:
        return True

    # Allow ONE realism refresh
    if turns in (0, 5):
        return True

    return False

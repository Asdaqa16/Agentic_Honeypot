def choose_strategy(session, incoming_text, reflection=None):
    intel = session.get("intelligence", {})
    agent_state = session.get("agent_state", {})
    turns = agent_state.get("turns", 0)

    if reflection == "progress":
        return "delay"

    if reflection == "stall":
        return "extract_identity"

    if not intel.get("upiIds"):
        return "extract_payment"

    if turns < 10:
        return "delay"

    return "terminate"

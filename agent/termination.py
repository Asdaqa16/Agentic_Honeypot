def should_terminate(session, agent_state):
    turns = agent_state.get("turns", 0)
    stalls = agent_state.get("stall_count", 0)

    if stalls >= 3:
        return True

    if turns >= 15:
        return True

    return False

def reflect(prev_intel, new_intel, prev_strategy):
    """
    Decide whether the last move made progress.
    """

    if new_intel != prev_intel:
        return "progress"

    if prev_strategy == "delay":
        return "stall"

    return "retry"

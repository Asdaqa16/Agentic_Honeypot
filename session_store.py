import json
from redis_client import redis_client

SESSION_TTL_SECONDS = 3600  # 1 hour


# ----------------------------
# Get or create session
# ----------------------------
def get_session(session_id: str) -> dict:
    key = f"session:{session_id}"
    raw = redis_client.get(key)

    if raw:
        return json.loads(raw)

    # ----------------------------
    # FIRST MESSAGE → create session
    # ----------------------------
    session = {
        "messages": [],
        "agent_state": {
            "turns": 0,
            "stall_count": 0,
            "current_strategy": "delay",
            "last_language": "english",
            "used_templates": [],
            "llm_calls": 0
        },
        "intelligence": {
            "upiIds": [],
            "phoneNumbers": [],
            "phishingLinks": [],
            "suspiciousKeywords": []
        },
        "scam_detected": True,
        "finalized": False
    }

    redis_client.setex(
        key,
        SESSION_TTL_SECONDS,
        json.dumps(session)
    )

    return session


# ----------------------------
# Save updated session
# ----------------------------
def save_session(session_id: str, session: dict) -> None:
    key = f"session:{session_id}"

    redis_client.setex(
        key,
        SESSION_TTL_SECONDS,
        json.dumps(session)
    )

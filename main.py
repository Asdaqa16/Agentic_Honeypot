from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import requests

from session_store import get_session, save_session
from agent.agent import agent_step

app = FastAPI()


# ----------------------------
# Health check
# ----------------------------
@app.get("/")
def health():
    return {"status": "backend running"}


# ----------------------------
# Request models
# ----------------------------
class Message(BaseModel):
    sender: str
    text: str
    timestamp: int


class HoneypotRequest(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: list | None = []
    metadata: dict | None = {}


# ----------------------------
# Honeypot API
# ----------------------------
@app.post("/api/honeypot")
def honeypot(
    body: HoneypotRequest,
    x_api_key: str = Header(None, alias="x-api-key")
):
    # 1️⃣ API key check
    if x_api_key != "dev_key":
        raise HTTPException(status_code=401, detail="Invalid API key")

    session_id = body.sessionId
    incoming_text = body.message.text

    # 2️⃣ Load or create session (Redis)
    session = get_session(session_id)

    # 3️⃣ Run agent step
    agent_output = agent_step(session, incoming_text)

    # 4️⃣ Persist updated session
    save_session(session_id, session)

    # 5️⃣ Mandatory final callback (ONLY ONCE, RACE-SAFE)
    if agent_output["should_finalize"] and not session.get("finalized", False):
        # 🔒 Mark finalized FIRST to prevent duplicate callbacks
        session["finalized"] = True
        save_session(session_id, session)

        payload = {
            "sessionId": session_id,
            "scamDetected": session.get("scam_detected", True),
            "totalMessagesExchanged": len(session["messages"]),
            "extractedIntelligence": {
                "bankAccounts": session["intelligence"].get("bankAccounts", []),
                "upiIds": session["intelligence"].get("upiIds", []),
                "phishingLinks": session["intelligence"].get("phishingLinks", []),
                "phoneNumbers": session["intelligence"].get("phoneNumbers", []),
                "suspiciousKeywords": session["intelligence"].get("suspiciousKeywords", [])
            },
            "agentNotes": agent_output["agent_notes"]
        }

        try:
            requests.post(
                "https://hackathon.guvi.in/api/updateHoneyPotFinalResult",
                json=payload,
                timeout=5
            )
        except Exception as e:
            # Do NOT crash API even if callback fails
            print("Callback failed:", e)

    # 6️⃣ Return agent reply (SPEC FORMAT)
    return {
        "status": "success",
        "reply": agent_output["reply"]
    }

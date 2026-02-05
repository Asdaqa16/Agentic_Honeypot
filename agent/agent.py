import json
from agent.templates import get_template_reply
from agent.llm_gate import should_use_llm
from agent.strategies import choose_strategy
from agent.persona import build_prompt
from agent.extraction import extract_intelligence
from agent.extraction import dedup_preserve_order
from agent.termination import should_terminate
from agent.reflection import reflect
import google.generativeai as genai
from agent.json_utils import safe_parse_json
import os, copy
from dotenv import load_dotenv
import time

LLM_WINDOW = []
LLM_MAX_CALLS = 4   # per 60 seconds
LLM_WINDOW_SECONDS = 60


load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def agent_step(session: dict, incoming_text: str) -> dict:
    agent_state = session.setdefault("agent_state", {})
    intelligence = session.setdefault("intelligence", {})
    messages = session.setdefault("messages", [])

    # Initialize state
    agent_state.setdefault("turns", 0)
    agent_state.setdefault("stall_count", 0)
    agent_state.setdefault("current_strategy", "delay")
    agent_state.setdefault("used_templates", [])
    agent_state.setdefault("last_language", "english")
    agent_state.setdefault("llm_calls", 0)
    language = agent_state["last_language"]  # often "english"

    # Append incoming message
    messages.append({"sender": "scammer", "text": incoming_text})

    prev_intel = intelligence.copy()
    prev_strategy = agent_state["current_strategy"]

    # Decide strategy
    strategy = choose_strategy(session, incoming_text)

    # -----------------------------
    # LLM RATE + GATING DECISION
    # -----------------------------
    now = time.time()

    # 🔒 Session-scoped LLM window (NOT global)
    llm_window = agent_state.setdefault("llm_window", [])
    llm_window[:] = [
        t for t in llm_window
        if now - t < LLM_WINDOW_SECONDS
    ]

    allow_llm = (
        len(llm_window) < LLM_MAX_CALLS
        and should_use_llm(strategy, agent_state)
    )


    # -----------------------------
    # RESPONSE GENERATION
    # -----------------------------
    reply_text = None
    language = agent_state["last_language"]

    if allow_llm:
        try:
            prompt = build_prompt(messages, strategy, incoming_text)
            resp = model.generate_content(prompt)
            raw = (resp.text or "").strip()

            if not raw:
                raise ValueError("Empty Gemini response")

            parsed = safe_parse_json(raw)

            if parsed and "reply" in parsed:
                reply_text = parsed["reply"]
                language = parsed.get("language", language)
            else:
                reply_text = raw

                # Language inference fallback
                if any(w in raw.lower() for w in ["hai", "kyun", "kyu", "nahi", "kya", "ka"]):
                    language = "hinglish"
                else:
                    language = "english"



            agent_state["llm_calls"] += 1
            LLM_WINDOW.append(time.time())

        except Exception:
            # Absolute safety: never crash
            reply_text = None

    # -----------------------------
    # TEMPLATE FALLBACK
    # -----------------------------
    if not reply_text:
        reply_text = get_template_reply(
            strategy,
            language,
            agent_state["used_templates"]
        )
        agent_state["used_templates"].append(reply_text)

    agent_state["last_language"] = language

    # Append agent reply
    messages.append({"sender": "agent", "text": reply_text})

    # -----------------------------
    # INTELLIGENCE EXTRACTION
    # -----------------------------
    intel_delta = extract_intelligence(incoming_text + " " + reply_text)

    for k, v in intel_delta.items():
        intelligence.setdefault(k, []).extend(v)
        intelligence[k] = dedup_preserve_order(intelligence[k])

    # -----------------------------
    # REFLECTION
    # -----------------------------
    reflection = reflect(prev_intel, intelligence, prev_strategy)

    if reflection == "stall":
        agent_state["stall_count"] += 1
    else:
        agent_state["stall_count"] = 0

    # Update state
    agent_state["current_strategy"] = choose_strategy(
        session,
        incoming_text,
        reflection=reflection
    )
    agent_state["turns"] += 1

    # -----------------------------
    # TERMINATION
    # -----------
    finalize = should_terminate(session, agent_state)

    # -----------------------------
    # FINAL RETURN (MUST ALWAYS RUN)
    # -----------------------------
    return {
        "reply": reply_text,
        "should_finalize": finalize,
        "agent_notes": generate_agent_notes(session)
    }



def generate_agent_notes(session: dict) -> str:
    intel = session.get("intelligence", {})
    keywords = intel.get("suspiciousKeywords", [])
    upis = intel.get("upiIds", [])
    links = intel.get("phishingLinks", [])
    phones = intel.get("phoneNumbers", [])

    notes = []

    # Urgency / pressure tactics
    if any(k in keywords for k in ["urgent", "final warning", "blocked", "suspended"]):
        notes.append("urgency tactics")

    # Payment redirection
    if upis:
        notes.append("payment redirection")

    # Phishing attempts
    if links:
        notes.append("phishing links")

    # Direct contact extraction
    if phones:
        notes.append("direct contact solicitation")

    if not notes:
        return "Scammer attempted social engineering"

    return "Scammer used " + " and ".join(notes)

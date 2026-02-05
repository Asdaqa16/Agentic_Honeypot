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

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("models/gemini-2.5-flash")

def agent_step(session: dict, incoming_text: str) -> dict:
    agent_state = session.setdefault("agent_state", {})
    intelligence = session.setdefault("intelligence", {})
    messages = session.setdefault("messages", [])

    agent_state.setdefault("used_templates", [])
    agent_state.setdefault("turns", 0)
    agent_state.setdefault("stall_count", 0)
    agent_state.setdefault("current_strategy", "delay")

    prev_intel = copy.deepcopy(intelligence)
    prev_strategy = agent_state["current_strategy"]

    strategy = choose_strategy(session, incoming_text)

    # Decide LLM vs Template
    if should_use_llm(strategy, agent_state):
        prompt = build_prompt(messages, strategy, incoming_text)
        raw = model.generate_content(prompt).text.strip()

        
    parsed = safe_parse_json(raw)   

    if parsed and "reply" in parsed:
        language = parsed.get("language", "english")
        reply_text = parsed["reply"]
    else:
        # HARD fallback — never crash
        language = agent_state.get("last_language", "english")
        reply_text = get_template_reply(
            strategy,
            language,
            agent_state["used_templates"]
        )

    agent_state["last_language"] = language

    # Intelligence extraction
    intel_delta = extract_intelligence(incoming_text + " " + reply_text)
    for k, v in intel_delta.items():
        intelligence.setdefault(k, []).extend(v)
        intelligence[k] = dedup_preserve_order(intelligence[k])


    # Reflection
    reflection = reflect(prev_intel, intelligence, prev_strategy)
    if reflection == "stall":
        agent_state["stall_count"] += 1
    else:
        agent_state["stall_count"] = 0

    agent_state["current_strategy"] = choose_strategy(
        session, incoming_text, reflection=reflection
    )
    agent_state["turns"] += 1

    finalize = should_terminate(session, agent_state)

    return {
        "reply": reply_text,
        "updated_agent_state": agent_state,
        "intelligence_delta": intel_delta,
        "should_finalize": finalize,
        "agent_notes": f"lang={language}, strat={strategy}, llm={should_use_llm(strategy, agent_state)}"
    }
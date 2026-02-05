import random

TEMPLATES = {
    "english": {
        "delay": [
            "Wait a second, I’m trying to understand this.",
            "Give me a moment, this is confusing.",
            "I’m not sure what you mean yet.",
            "Can you explain this step by step?",
            "I need a minute to check something.",
            "This is a bit unclear to me.",
            "Hold on, I’m trying to figure this out.",
            "Let me understand properly first."
        ],
        "verify_claim": [
            "Why is this happening all of a sudden?",
            "I didn’t receive any bank message about this.",
            "Which bank branch are you calling from?",
            "Can you explain why my account is affected?",
            "This doesn’t make sense to me yet.",
            "How did this issue start?",
            "Why wasn’t I informed earlier?",
            "Are you sure this is related to my account?"
        ],
    },
    "hinglish": {
        "delay": [
            "Ek minute ruko, samajhne do.",
            "Thoda time do, ye clear nahi hai.",
            "Main abhi samajh nahi pa raha hoon.",
            "Zara detail mein batao na.",
            "Ruko, main check kar raha hoon.",
            "Abhi clear nahi lag raha mujhe.",
            "Thoda ruk jao, main dekh raha hoon.",
            "Ek second, ye confuse kar raha hai."
        ],
        "verify_claim": [
            "Ye achanak kaise ho gaya?",
            "Mujhe bank se koi message nahi aaya.",
            "Aap kaunse branch se bol rahe ho?",
            "Mera account ismein kaise aa gaya?",
            "Ye sab ka reason kya hai?",
            "Pehle aisa kabhi nahi hua.",
            "Aapne pehle inform kyun nahi kiya?",
            "Ye kaise confirm ho raha hai?"
        ],
    }
}

def get_template_reply(strategy, language, used_lines):
    options = [
        line for line in TEMPLATES[language][strategy]
        if line not in used_lines
    ]

    if not options:
        return random.choice(TEMPLATES[language][strategy])

    return random.choice(options)

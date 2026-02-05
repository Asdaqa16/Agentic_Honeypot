import re

def dedup_preserve_order(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def extract_intelligence(text):
    return {
        "upiIds": re.findall(r"\b[\w.-]+@[\w]+\b", text),
        "phoneNumbers": re.findall(r"\b\d{10}\b", text),
        "phishingLinks": re.findall(r"https?://\S+", text),
        "suspiciousKeywords": [
            w for w in ["urgent", "verify", "blocked", "suspended"]
            if w in text.lower()
        ]
    }

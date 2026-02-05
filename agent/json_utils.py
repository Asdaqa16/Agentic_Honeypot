import json
import re

def safe_parse_json(text: str):
    if not text:
        return None

    # Remove markdown code fences
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text)
    text = re.sub(r"```$", "", text)

    # Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # Extract JSON object manually
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return None
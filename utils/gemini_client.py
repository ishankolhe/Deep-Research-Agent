import os
import json
import time
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

_model = genai.GenerativeModel(MODEL_NAME)

# Free-tier RPM is low (single digits to low tens depending on model/tier).
# Space calls out so we don't trip 429s and fall into long retry backoffs.
MIN_SECONDS_BETWEEN_CALLS = float(os.environ.get("GEMINI_MIN_SECONDS_BETWEEN_CALLS", "4"))
_last_call_ts = 0.0


def _call(prompt: str, retries: int = 3, delay: float = 8.0) -> str:
    """Basic call with pacing + retry/backoff to survive free-tier rate limits (429s)."""
    global _last_call_ts
    last_err = None
    for attempt in range(retries):
        wait = MIN_SECONDS_BETWEEN_CALLS - (time.time() - _last_call_ts)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = _model.generate_content(prompt)
            _last_call_ts = time.time()
            return resp.text
        except Exception as e:
            last_err = e
            _last_call_ts = time.time()
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"Gemini call failed after {retries} retries: {last_err}")


def generate_text(prompt: str) -> str:
    return _call(prompt)


def generate_json(prompt: str, schema_hint: str) -> dict | list:
    """
    Ask Gemini for strict JSON. schema_hint is a short description/example of the
    expected shape, appended to the prompt. Strips markdown code fences if present.
    """
    full_prompt = (
        f"{prompt}\n\n"
        f"Respond with ONLY valid JSON matching this shape, no prose, no markdown fences:\n"
        f"{schema_hint}"
    )
    raw = _call(full_prompt)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # last-resort: find the first { or [ and last } or ]
        start = min([i for i in [cleaned.find("{"), cleaned.find("[")] if i != -1], default=-1)
        end = max(cleaned.rfind("}"), cleaned.rfind("]"))
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end + 1])
        raise

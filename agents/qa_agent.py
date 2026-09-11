from utils.gemini_client import generate_json


def answer_followup(question: str, research_results: list[dict]) -> dict:
    """
    Answers a follow-up question about an existing report using ONLY the facts
    already gathered during its research (no new web search) — fast, free, and
    stays grounded in the report's own sources instead of the model's general
    knowledge. Returns {"answer": str, "supported": bool}.
    """
    facts_lines = []
    citation_map = {}
    counter = 1
    for r in research_results or []:
        for f in r.get("facts", []):
            url = f.get("source_url")
            if url not in citation_map:
                citation_map[url] = counter
                counter += 1
            n = citation_map[url]
            facts_lines.append(f"- {f.get('text', '')} [{n}]")
    facts_text = "\n".join(facts_lines)

    prompt = (
        f"You are answering a follow-up question about a research report, using ONLY "
        f"the facts gathered during that research below (do not use outside knowledge, "
        f"do not invent facts). Keep citation numbers like [1] inline where relevant.\n\n"
        f"FACTS:\n{facts_text}\n\n"
        f"QUESTION: {question}\n\n"
        f"If the facts above don't contain enough information to answer well, say so "
        f"plainly and suggest running a new research query on that specific angle "
        f"instead of guessing."
    )
    schema = '{"answer": "your answer here", "supported": true}'
    try:
        result = generate_json(prompt, schema)
    except Exception:
        result = {"answer": "Sorry, couldn't process that question right now — try again.",
                   "supported": False}
    if not isinstance(result, dict):
        result = {"answer": str(result), "supported": False}
    result.setdefault("answer", "")
    result.setdefault("supported", False)
    return result

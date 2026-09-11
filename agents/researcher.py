from utils.tavily_client import search
from utils.gemini_client import generate_json


def research_subquestion(subquestion: str) -> dict:
    """
    Searches the web for a sub-question, then makes ONE Gemini call covering all
    sources together (to stay within free-tier daily request caps), extracting
    factual bullets tagged with which source they came from.
    Returns: {"subquestion": ..., "facts": [{"text": ..., "source_url": ..., "source_title": ...}]}
    """
    sources = search(subquestion, max_results=4)
    sources = [s for s in sources if s.get("content")]
    if not sources:
        return {"subquestion": subquestion, "facts": []}

    combined = "\n\n".join(
        f"SOURCE {i+1} ({s['title']}):\n{s['content'][:1500]}"
        for i, s in enumerate(sources)
    )
    prompt = (
        f"Sub-question: \"{subquestion}\"\n\n"
        f"Below are {len(sources)} web sources. Extract 2-4 short factual bullet "
        f"points per source that are relevant to answering the sub-question. "
        f"Keep bullets concise and specific (include numbers/dates where present). "
        f"Skip a source entirely if it has no relevant info.\n\n{combined}"
    )
    schema = (
        '[{"text": "fact bullet", "source_index": 1}, '
        '{"text": "another fact", "source_index": 2}]'
    )
    try:
        items = generate_json(prompt, schema)
    except Exception:
        items = []

    facts = []
    for item in items if isinstance(items, list) else []:
        try:
            idx = int(item.get("source_index", 0)) - 1
        except (TypeError, ValueError):
            continue
        if 0 <= idx < len(sources):
            facts.append({
                "text": str(item.get("text", "")),
                "source_url": sources[idx]["url"],
                "source_title": sources[idx]["title"],
            })
    return {"subquestion": subquestion, "facts": facts}

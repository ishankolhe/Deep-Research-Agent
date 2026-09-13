from utils.tavily_client import search
from utils.academic_search import search_academic
from utils.gemini_client import generate_json


def _extract_facts(subquestion: str, sources: list[dict]) -> list[dict]:
    """
    Shared extraction step: one Gemini call covering all sources together (stays
    within free-tier daily request caps), tagging each fact with which source it
    came from so citation metadata (author/year/venue for academic sources, plain
    URL for web) survives into the final report.
    """
    sources = [s for s in sources if s.get("abstract") or s.get("content")]
    if not sources:
        return []

    combined = "\n\n".join(
        f"SOURCE {i+1} ({s['title']}):\n{(s.get('abstract') or s.get('content', ''))[:1500]}"
        for i, s in enumerate(sources)
    )
    prompt = (
        f"Sub-question: \"{subquestion}\"\n\n"
        f"Below are {len(sources)} sources. Extract 2-4 short factual bullet "
        f"points per source that are relevant to answering the sub-question. "
        f"Keep bullets concise and specific (include numbers/dates/named systems "
        f"where present). Skip a source entirely if it has no relevant info.\n\n{combined}"
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
            s = sources[idx]
            facts.append({
                "text": str(item.get("text", "")),
                "source_url": s.get("url", ""),
                "source_title": s.get("title", ""),
                "source_type": s.get("source_type", "web"),
                "authors": s.get("authors", []),
                "year": s.get("year", ""),
                "venue": s.get("venue", ""),
            })
    return facts


def research_subquestion(subquestion: str) -> dict:
    """Fast mode: general web search via Tavily."""
    sources = search(subquestion, max_results=4)
    for s in sources:
        s["source_type"] = "web"
    facts = _extract_facts(subquestion, sources)
    return {"subquestion": subquestion, "facts": facts}


def research_subquestion_academic(subquestion: str, min_academic: int = 2) -> dict:
    """
    Deep mode: prioritizes peer-reviewed/preprint sources (arXiv + Semantic
    Scholar). Falls back to general web search only to fill remaining slots
    when academic coverage is thin for a niche sub-question — per-fact
    source_type stays tagged so the writer can distinguish primary research
    from secondary/background sources.
    """
    papers = search_academic(subquestion, max_results=4)
    sources = list(papers)
    if len(papers) < min_academic:
        web_sources = search(subquestion, max_results=4 - len(papers))
        for s in web_sources:
            s["source_type"] = "web"
        sources.extend(web_sources)
    facts = _extract_facts(subquestion, sources)
    return {"subquestion": subquestion, "facts": facts}

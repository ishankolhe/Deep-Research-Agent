from utils.gemini_client import generate_text


def build_citation_map(research_results: list[dict]) -> dict:
    """
    Walks research_results in the same deterministic order used when writing the
    report, assigning each unique source URL a citation number. Shared by the
    writer (to number citations in the text) and the API (to expose a structured
    citations list for clickable source jumping) so numbering always matches.
    Returns: {url: {"number": n, "title": str}}
    """
    citation_map = {}
    counter = 1
    for r in research_results:
        for f in r["facts"]:
            key = f["source_url"]
            if key not in citation_map:
                citation_map[key] = {"number": counter, "title": f.get("source_title", "")}
                counter += 1
    return citation_map


def write_report(query: str, research_results: list[dict]) -> str:
    """
    Turns all gathered facts + citations into a structured Markdown report.
    """
    citation_map = build_citation_map(research_results)
    facts_block = []
    for r in research_results:
        facts_block.append(f"\n### Sub-question: {r['subquestion']}")
        for f in r["facts"]:
            n = citation_map[f["source_url"]]["number"]
            facts_block.append(f"- {f['text']} [{n}]")
    facts_text = "\n".join(facts_block)

    references = "\n".join(
        f"[{c['number']}] {url}"
        for url, c in sorted(citation_map.items(), key=lambda x: x[1]["number"])
    )

    prompt = (
        f"Write a structured research report answering: \"{query}\"\n\n"
        f"Use ONLY the facts below (with their citation numbers in brackets) as source "
        f"material — do not invent facts. Organize the report with these Markdown "
        f"sections: '## Introduction', '## Key findings' (with a subsection per "
        f"sub-question), '## Analysis and comparisons', '## Conclusion'. "
        f"Keep citation numbers like [1] inline where you use a fact. Be specific and "
        f"insight-driven, not just a bullet dump — synthesize patterns across sources.\n\n"
        f"FACTS:\n{facts_text}\n"
    )
    body = generate_text(prompt)
    return f"{body}\n\n## References\n{references}\n"

from utils.gemini_client import generate_json


def find_gaps(original_query: str, research_results: list[dict]) -> list[str]:
    """
    Looks at everything gathered so far and asks whether any important angle
    on the original query is still under-covered. Returns 0-3 new follow-up
    search queries, or an empty list if coverage looks sufficient.
    """
    summary_lines = []
    for r in research_results:
        summary_lines.append(f"- {r['subquestion']}: {len(r['facts'])} facts found")
    summary = "\n".join(summary_lines)

    prompt = (
        f"Original research question: \"{original_query}\"\n\n"
        f"Sub-questions researched so far and how many facts were found for each:\n"
        f"{summary}\n\n"
        f"Are there any important angles on the original question that are missing "
        f"or under-covered (e.g. a sub-question with very few facts, or an obvious "
        f"angle nobody asked about)? List 0 to 3 new, specific follow-up search queries "
        f"to fill those gaps. If coverage is already good, return an empty list."
    )
    schema = '["follow-up query 1", "follow-up query 2"]'
    try:
        result = generate_json(prompt, schema)
    except Exception:
        result = []
    return [str(q) for q in result][:3]

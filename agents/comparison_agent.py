from utils.gemini_client import generate_json


def build_comparison_table(query: str, research_results: list[dict]) -> str | None:
    """
    Scans gathered facts for named systems/methods/approaches. If 2+ distinct
    named things are identifiable, returns a ready-to-embed Markdown table
    string (reusing the existing table renderer already built for the report
    exporters). Returns None if there's nothing meaningful to compare —
    callers should skip the section entirely rather than force an empty table.
    """
    all_facts = []
    for r in research_results:
        for f in r["facts"]:
            all_facts.append(f["text"])
    facts_text = "\n".join(f"- {t}" for t in all_facts)

    prompt = (
        f"Research topic: \"{query}\"\n\n"
        f"Facts gathered:\n{facts_text}\n\n"
        f"Identify distinct NAMED systems, methods, models, or approaches mentioned "
        f"in these facts that are directly relevant to comparing options for this "
        f"topic. If you can identify 2 or more such named things with enough facts "
        f"to compare, return a comparison table. If fewer than 2 clear named things "
        f"exist, return an empty rows list — do not force a comparison that isn't "
        f"supported by the facts.\n\n"
        f"Choose comparison columns that fit what the facts actually cover — for "
        f"topics involving autonomous systems/agents, good columns (where facts "
        f"support them) include: Year, Domain, Hypothesis generation, Experiment "
        f"execution, Human intervention, Reported performance, Reproducibility, "
        f"Major limitation. For other topic types, adapt columns to what's actually "
        f"comparable. Only use columns you have real facts for — do not invent."
    )
    schema = (
        '{"columns": ["System", "Year", "..."], '
        '"rows": [["value", "value", "..."], ["value", "value", "..."]]}'
    )
    try:
        result = generate_json(prompt, schema)
    except Exception:
        return None

    if not isinstance(result, dict):
        return None
    columns = result.get("columns", [])
    rows = result.get("rows", [])
    if not columns or not rows or len(rows) < 1:
        return None

    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = "\n".join(
        "| " + " | ".join(str(c) for c in row[:len(columns)]) + " |"
        for row in rows
    )
    return f"{header}\n{separator}\n{body}"

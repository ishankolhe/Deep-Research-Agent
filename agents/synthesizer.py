from utils.gemini_client import generate_text


def build_citation_map(research_results: list[dict]) -> dict:
    """
    Walks research_results in the same deterministic order used when writing the
    report, assigning each unique source URL a citation number. Shared by the
    writer (to number citations in the text) and the API (to expose a structured
    citations list for clickable source jumping) so numbering always matches.
    Returns: {url: {"number": n, "title": str, "authors": [...], "year": str,
                     "venue": str, "source_type": "web"|"academic"}}
    """
    citation_map = {}
    counter = 1
    for r in research_results:
        for f in r["facts"]:
            key = f["source_url"]
            if key not in citation_map:
                citation_map[key] = {
                    "number": counter,
                    "title": f.get("source_title", ""),
                    "authors": f.get("authors", []),
                    "year": f.get("year", ""),
                    "venue": f.get("venue", ""),
                    "source_type": f.get("source_type", "web"),
                }
                counter += 1
    return citation_map


def _facts_and_references(research_results: list[dict]) -> tuple[str, str]:
    citation_map = build_citation_map(research_results)
    facts_block = []
    for r in research_results:
        facts_block.append(f"\n### Sub-question: {r['subquestion']}")
        for f in r["facts"]:
            n = citation_map[f["source_url"]]["number"]
            tag = " (academic source)" if f.get("source_type") == "academic" else ""
            facts_block.append(f"- {f['text']} [{n}]{tag}")
    facts_text = "\n".join(facts_block)

    # Keep the on-page reference format as "[n] <url>" — the exporters' regex
    # expects exactly this shape to render clickable hyperlinks. Richer metadata
    # (authors/year/venue) is exposed separately via the API's citations list.
    references = "\n".join(
        f"[{c['number']}] {url}"
        for url, c in sorted(citation_map.items(), key=lambda x: x[1]["number"])
    )
    return facts_text, references


def write_report(query: str, research_results: list[dict]) -> str:
    """Fast mode: single-pass structured report."""
    facts_text, references = _facts_and_references(research_results)

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


def write_deep_report(query: str, research_results: list[dict],
                       comparison_table_md: str | None = None) -> str:
    """
    Deep/academic mode: produces a rigorous multi-section report across a few
    grounded calls instead of one shot, so each section gets focused attention
    rather than being compressed into a single generic pass. Every call receives
    the full fact set so nothing is written ungrounded.
    """
    facts_text, references = _facts_and_references(research_results)

    common_instructions = (
        f"You are writing part of a rigorous, academic-standard research report "
        f"answering: \"{query}\"\n\n"
        f"Use ONLY the facts below (citation numbers in brackets) — never invent facts, "
        f"numbers, or claims. Keep citation numbers like [1] inline wherever you use a "
        f"fact. Where a claim is well-supported by multiple independent facts, you may "
        f"mark it '**[Strong evidence]**'; where it rests on a single source or thin "
        f"data, mark it '**[Limited evidence]**'; where you are inferring beyond what "
        f"any single fact states (synthesizing a pattern across sources), say so "
        f"explicitly (e.g. 'Taken together, this suggests...') rather than presenting "
        f"the inference as a directly reported fact.\n\n"
        f"FACTS:\n{facts_text}\n\n"
    )

    part1 = generate_text(
        common_instructions +
        "Write these sections:\n"
        "'## Executive Summary' — 1 tight paragraph previewing the answer.\n"
        "'## Research Question and Definitions' — precisely define the key terms "
        "and concepts in this topic, and explicitly distinguish related-but-different "
        "capabilities or claims that are commonly conflated in this domain (e.g. "
        "doing X once vs. doing X reliably; claiming Y vs. demonstrating Y "
        "experimentally). This section should sharpen exactly what is being asked.\n"
        "'## What Counts as a Genuine Answer' — separate from the definitions above, "
        "spell out what would actually need to be TRUE/demonstrated for this "
        "question to be answered affirmatively vs. negatively — i.e. don't let "
        "completing one isolated sub-task be mistaken for answering the whole "
        "question.\n"
        "'## Evaluation Criteria' — state the explicit criteria that would count as "
        "a genuine, well-supported answer to this question (not just 'is it "
        "interesting' — think rigor, reproducibility, independence of evidence, etc., "
        "adapted to this specific topic)."
    )

    comparison_block = (
        f"\n\nA structured comparison table has already been built from the facts — "
        f"embed it VERBATIM under the landscape section heading, then add 1-2 "
        f"paragraphs interpreting what it shows:\n\n{comparison_table_md}\n"
        if comparison_table_md else
        "\n\nNo multi-system comparison table was generated (facts didn't support "
        "one) — instead describe the landscape of approaches in prose.\n"
    )
    part2 = generate_text(
        common_instructions +
        "Write these sections:\n"
        "'## System and Approach Landscape' — the named systems/methods/approaches "
        "most directly relevant to this question, and what each one actually does "
        "(not just a list — explain what evidence each provides)." + comparison_block +
        "'## Empirical Evidence and Benchmarks' — extract actual reported numbers "
        "(scores, rates, counts) and explain what each number means; do not treat "
        "differently-scaled benchmarks as directly comparable without saying so.\n"
        "'## Failure Modes and Limitations' — concrete, specific failure modes from "
        "the facts (not generic caveats), citing which source reported each."
    )

    part3 = generate_text(
        common_instructions +
        "Write these sections:\n"
        "'## Novelty Analysis' — how novelty is (or isn't) evaluated for claims in "
        "this domain, and whether 'new to the system' is being conflated with 'new "
        "to the field' anywhere in the facts.\n"
        "'## Human Intervention and Autonomy' — for each major system/claim, how "
        "much human involvement was actually required versus genuinely independent "
        "operation, based on the facts.\n"
        "'## Reproducibility' — what's actually reproducible (code/data/methodology "
        "available) versus merely reported as working once."
    )

    part4 = generate_text(
        common_instructions +
        "Write these sections:\n"
        "'## Critical Synthesis and Conflicting Evidence' — if facts from different "
        "sources disagree or point different directions, name the disagreement "
        "explicitly and weigh which evidence is stronger and why (methodology, "
        "sample size, independence of the source) rather than just listing both.\n"
        "'## Research Gaps' — unresolved problems evident from the facts gathered "
        "(not generic 'more research is needed') — derive these from what the "
        "sources actually failed to demonstrate or address.\n"
        "'## Future Directions' — distinct from the gaps above, what concrete next "
        "steps or approaches could plausibly close those gaps.\n"
        "'## Final Answer and Confidence Assessment' — explicitly and directly "
        "answer the original research question (not a vague 'it's promising but "
        "has limitations' — state what's demonstrated, what's not, what's needed "
        "for the gap to close), then give: Overall confidence level (High/Moderate/"
        "Low), the strongest evidence FOR your answer, the strongest evidence "
        "AGAINST it, the biggest remaining uncertainty, and the most important "
        "unresolved question."
    )

    body = "\n\n".join([part1, part2, part3, part4])
    return f"{body}\n\n## References\n{references}\n"

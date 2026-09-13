from utils.gemini_client import generate_json


def plan_subquestions(query: str, deep_mode: bool = False) -> list[str]:
    if not deep_mode:
        prompt = (
            f"A user wants a deep research report on: \"{query}\"\n"
            f"Break this into 4 to 6 focused, non-overlapping sub-questions that together "
            f"cover the topic well (background, current state, comparisons/tradeoffs, "
            f"data/trends, implications). Each sub-question should be answerable via web search."
        )
    else:
        prompt = (
            f"A user wants a RIGOROUS, ACADEMIC-STANDARD research report on: \"{query}\"\n\n"
            f"Generate 7-8 sub-questions, each targeting ONE of these analytical dimensions "
            f"applied specifically to this topic (adapt the wording to the topic, but cover "
            f"every dimension — do not skip any):\n"
            f"1. Precise definitions and scope of the key terms/concepts in this question\n"
            f"2. What specific named systems, methods, or papers most directly address this question\n"
            f"3. Quantitative/empirical results and benchmarks reported for those systems\n"
            f"4. Documented failure modes, limitations, or negative results\n"
            f"5. Novelty — how is novelty evaluated, and can existing approaches be distinguished "
            f"from merely rediscovering prior work\n"
            f"6. Reproducibility — code/data availability, independent replication\n"
            f"7. Degree of human intervention required versus genuine autonomy/independence\n"
            f"8. Points of disagreement or conflicting evidence between sources\n\n"
            f"Each sub-question must be specific enough to search for directly (name concepts "
            f"from the topic, not generic phrasing)."
        )
    schema = '["sub-question 1", "sub-question 2", ...]'
    result = generate_json(prompt, schema)
    if isinstance(result, dict) and "questions" in result:
        result = result["questions"]
    return [str(q) for q in result]

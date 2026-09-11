from utils.gemini_client import generate_json


def plan_subquestions(query: str) -> list[str]:
    prompt = (
        f"A user wants a deep research report on: \"{query}\"\n"
        f"Break this into 4 to 6 focused, non-overlapping sub-questions that together "
        f"cover the topic well (background, current state, comparisons/tradeoffs, "
        f"data/trends, implications). Each sub-question should be answerable via web search."
    )
    schema = '["sub-question 1", "sub-question 2", ...]'
    result = generate_json(prompt, schema)
    if isinstance(result, dict) and "questions" in result:
        result = result["questions"]
    return [str(q) for q in result]

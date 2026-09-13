import os
from tavily import TavilyClient

_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

_call_count = 0


def reset_call_count():
    global _call_count
    _call_count = 0


def get_call_count() -> int:
    return _call_count


def search(query: str, max_results: int = 4, depth: str = "basic") -> list[dict]:
    """
    Returns a list of {title, url, content} dicts.
    depth="basic" costs 1 credit, "advanced" costs 2 credits but extracts fuller content.
    """
    global _call_count
    _call_count += 1
    resp = _client.search(query=query, search_depth=depth, max_results=max_results)
    results = []
    for r in resp.get("results", []):
        results.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
        })
    return results

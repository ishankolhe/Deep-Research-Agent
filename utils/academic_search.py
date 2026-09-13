import requests
import xml.etree.ElementTree as ET

ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

_call_count = 0


def reset_call_count():
    global _call_count
    _call_count = 0


def get_call_count() -> int:
    return _call_count


def search_arxiv(query: str, max_results: int = 5) -> list[dict]:
    """
    arXiv's API needs no key. Returns preprints with real authors/year/URL —
    good primary-source coverage for CS/ML topics, weaker for older/less
    technical claims than Semantic Scholar's broader index.
    """
    try:
        resp = requests.get(
            "http://export.arxiv.org/api/query",
            params={"search_query": f"all:{query}", "start": 0,
                    "max_results": max_results, "sortBy": "relevance"},
            timeout=15,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        papers = []
        for entry in root.findall("atom:entry", ARXIV_NS):
            title = (entry.findtext("atom:title", default="", namespaces=ARXIV_NS) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ARXIV_NS) or "").strip()
            published = entry.findtext("atom:published", default="", namespaces=ARXIV_NS) or ""
            year = published[:4] if published else ""
            url = entry.findtext("atom:id", default="", namespaces=ARXIV_NS) or ""
            authors = [a.findtext("atom:name", default="", namespaces=ARXIV_NS)
                       for a in entry.findall("atom:author", ARXIV_NS)]
            if title:
                papers.append({
                    "title": title.replace("\n", " ").strip(),
                    "abstract": summary.replace("\n", " ").strip()[:1200],
                    "year": year,
                    "authors": [a for a in authors if a],
                    "venue": "arXiv preprint",
                    "url": url,
                    "source_type": "academic",
                })
        return papers
    except Exception:
        return []


def search_semantic_scholar(query: str, max_results: int = 5) -> list[dict]:
    """
    Broader index than arXiv (includes published venues, citation counts).
    No key required at low request volume, but can rate-limit under load —
    caller should treat failures as non-fatal and fall back to arXiv/web.
    """
    try:
        resp = requests.get(
            "https://api.semanticscholar.org/graph/v1/paper/search",
            params={"query": query, "limit": max_results,
                    "fields": "title,abstract,year,authors,venue,url,externalIds"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        papers = []
        for p in data:
            if not p.get("title"):
                continue
            doi = (p.get("externalIds") or {}).get("DOI", "")
            papers.append({
                "title": p["title"],
                "abstract": (p.get("abstract") or "")[:1200],
                "year": str(p.get("year") or ""),
                "authors": [a.get("name", "") for a in (p.get("authors") or [])],
                "venue": p.get("venue") or "",
                "url": p.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                "source_type": "academic",
            })
        return papers
    except Exception:
        return []


def search_academic(query: str, max_results: int = 5) -> list[dict]:
    """
    Tries Semantic Scholar first (richer metadata: venue, DOI), fills any
    remaining slots from arXiv. Returns [] if both fail — caller should
    fall back to general web search rather than block on this.
    """
    global _call_count
    _call_count += 1
    papers = search_semantic_scholar(query, max_results)
    if len(papers) < max_results:
        seen_titles = {p["title"].lower() for p in papers}
        for p in search_arxiv(query, max_results - len(papers)):
            if p["title"].lower() not in seen_titles:
                papers.append(p)
    return papers[:max_results]

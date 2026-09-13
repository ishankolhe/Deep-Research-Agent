class SourceCache:
    """
    Scoped to a single research job. When the same paper/page surfaces across
    multiple sub-question searches (common on a narrow deep-mode topic — e.g.
    "AI Scientist" showing up for both the "named systems" and "novelty"
    sub-questions), this skips a second Gemini extraction call on it and
    reuses the facts already extracted the first time instead.

    This is a deliberate quality/efficiency tradeoff: a fact extracted in the
    context of one sub-question may be slightly less tailored when reused for
    another, but every reused fact keeps its correct citation back to its real
    source, so accuracy isn't compromised — only phrasing specificity might be.
    """

    def __init__(self):
        self._facts_by_url: dict[str, list[dict]] = {}
        self.duplicate_sources_skipped = 0

    @staticmethod
    def _key(url: str) -> str:
        return (url or "").strip().lower().rstrip("/")

    def split_new_and_cached(self, sources: list[dict]) -> tuple[list[dict], list[dict]]:
        """Returns (sources_needing_extraction, facts_reused_from_cache)."""
        new_sources = []
        reused_facts = []
        for s in sources:
            key = self._key(s.get("url", ""))
            if key and key in self._facts_by_url:
                self.duplicate_sources_skipped += 1
                reused_facts.extend(self._facts_by_url[key])
            else:
                new_sources.append(s)
        return new_sources, reused_facts

    def store(self, url: str, facts: list[dict]):
        key = self._key(url)
        if key:
            self._facts_by_url[key] = facts

    def stats(self) -> dict:
        return {
            "unique_sources": len(self._facts_by_url),
            "duplicate_sources_skipped": self.duplicate_sources_skipped,
        }

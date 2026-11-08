"""
DuckDuckGo Zero-Key Search Provider using ddgs.
"""

from typing import List
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

from .base import SearchProvider, SearchHit

class DuckDuckGoProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        hits = []
        if DDGS is None:
            return hits
        seen = set()
        try:
            ddgs = DDGS()
            # News search for recent events/fixtures/scores
            try:
                for n in ddgs.news(query, max_results=max_results):
                    u = n.get("url", "")
                    if u and u not in seen and "bing.com/aclick" not in u:
                        hits.append(SearchHit(
                            title=n.get("title", ""),
                            url=u,
                            snippet=f"[{n.get('date', '')} - {n.get('source', '')}] {n.get('body', '')}",
                            date=n.get("date", ""),
                            source=n.get("source", "")
                        ))
                        seen.add(u)
            except Exception:
                pass

            # General text search
            for w in ddgs.text(query, max_results=max_results + 3):
                u = w.get("href", "")
                if u and u not in seen and "bing.com/aclick" not in u and "doubleclick.net" not in u:
                    hits.append(SearchHit(
                        title=w.get("title", ""),
                        url=u,
                        snippet=w.get("body", "")
                    ))
                    seen.add(u)
                    if len(hits) >= max_results:
                        break
        except Exception:
            pass
        return hits

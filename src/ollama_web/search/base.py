"""
Base interface and dataclasses for pluggable search engine providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class SearchHit:
    def __init__(self, title: str, url: str, snippet: str, date: str = "", source: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.date = date
        self.source = source

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "href": self.url,
            "body": self.snippet,
            "date": self.date,
            "source": self.source
        }

class SearchProvider(ABC):
    """Abstract base class for all search engine providers."""

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        pass

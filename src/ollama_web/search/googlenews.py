"""
Google News RSS Fallback Provider.
"""

import urllib.parse
import xml.etree.ElementTree as ET
from typing import List
import requests
from bs4 import BeautifulSoup
from .base import SearchProvider, SearchHit

class GoogleNewsRSSProvider(SearchProvider):
    def search(self, query: str, max_results: int = 5) -> List[SearchHit]:
        hits = []
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
            resp = requests.get(url, timeout=6)
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:max_results]:
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                pub_date = item.findtext("pubDate", "")
                raw_desc = item.findtext("description", "")
                desc = BeautifulSoup(raw_desc, "lxml").get_text(" ", strip=True) if raw_desc else ""
                hits.append(SearchHit(
                    title=title,
                    url=link,
                    snippet=f"[{pub_date}] {desc}",
                    date=pub_date,
                    source="Google News"
                ))
        except Exception:
            pass
        return hits

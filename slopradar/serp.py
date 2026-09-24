"""SerpApi Google Search client.

Plain HTTPS against https://serpapi.com/search.json. The key comes from the
SERPAPI_API_KEY environment variable and is never logged or written to disk.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

import requests

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"
ENV_KEY = "SERPAPI_API_KEY"


class SerpApiError(RuntimeError):
    pass


@dataclass
class SearchResult:
    query: str
    position: int
    title: str
    link: str
    displayed_link: str = ""
    snippet: str = ""
    source: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


def get_api_key(explicit: Optional[str] = None) -> str:
    key = explicit or os.environ.get(ENV_KEY, "").strip()
    if not key:
        raise SerpApiError(
            f"No SerpApi key found. Set {ENV_KEY} (get one at https://serpapi.com/manage-api-key)."
        )
    return key


def parse_organic_results(payload: Dict, query: str) -> List[SearchResult]:
    """Pull organic results out of a SerpApi Google response. Ads are ignored."""
    if payload.get("error"):
        raise SerpApiError(f"SerpApi error: {payload['error']}")
    results = []
    for item in payload.get("organic_results", []) or []:
        link = item.get("link") or ""
        if not link.startswith(("http://", "https://")):
            continue
        results.append(SearchResult(
            query=query,
            position=int(item.get("position") or len(results) + 1),
            title=item.get("title") or "",
            link=link,
            displayed_link=item.get("displayed_link") or "",
            snippet=item.get("snippet") or "",
            source=item.get("source") or "",
        ))
    results.sort(key=lambda r: r.position)
    return results


def parse_related_searches(payload: Dict, limit: int = 10) -> List[str]:
    """Queries Google itself suggests next to this one ("related searches" and
    "people also ask"). SlopRadar uses them to widen its sample of a niche the
    way real searchers do, instead of guessing variants."""
    seen, out = set(), []
    candidates = [r.get("query") for r in payload.get("related_searches", []) or []]
    candidates += [r.get("question") for r in payload.get("related_questions", []) or []]
    for q in candidates:
        if not q:
            continue
        key = " ".join(q.lower().split())
        if key in seen:
            continue
        seen.add(key)
        out.append(q.strip())
        if len(out) >= limit:
            break
    return out


def parse_news_results(payload: Dict, query: str) -> List[SearchResult]:
    """Google News results via SerpApi (engine=google_news).

    Top stories arrive either flat or as clusters with a nested ``stories``
    list; clusters are flattened in order so every article gets a rank.
    """
    if payload.get("error"):
        raise SerpApiError(f"SerpApi error: {payload['error']}")
    flat = []
    for item in payload.get("news_results", []) or []:
        if item.get("link"):
            flat.append(item)
        for story in item.get("stories", []) or []:
            if story.get("link"):
                flat.append(story)
    results = []
    for item in flat:
        link = item["link"]
        if not link.startswith(("http://", "https://")):
            continue
        source = item.get("source") or {}
        results.append(SearchResult(
            query=query,
            position=len(results) + 1,
            title=item.get("title") or "",
            link=link,
            displayed_link=source.get("name", "") if isinstance(source, dict) else str(source),
            snippet=item.get("date") or "",
            source=source.get("name", "") if isinstance(source, dict) else str(source),
        ))
    return results


@dataclass
class TrendQuery:
    query: str
    kind: str          # "rising" or "top"
    value: str         # as Google shows it: "Breakout", "+4,500%", "100"
    extracted_value: int


def parse_trends_related(payload: Dict, limit: int = 10) -> List[TrendQuery]:
    """Related queries from Google Trends (engine=google_trends,
    data_type=RELATED_QUERIES). Rising queries come first, strongest first,
    then top queries: what people are starting to search for right now."""
    if payload.get("error"):
        raise SerpApiError(f"SerpApi error: {payload['error']}")
    related = payload.get("related_queries") or {}
    out: List[TrendQuery] = []
    seen = set()
    for kind in ("rising", "top"):
        items = sorted(related.get(kind, []) or [], key=lambda i: -(i.get("extracted_value") or 0))
        for item in items:
            q = (item.get("query") or "").strip()
            if not q or q.lower() in seen:
                continue
            seen.add(q.lower())
            out.append(TrendQuery(q, kind, str(item.get("value", "")), int(item.get("extracted_value") or 0)))
    return out[:limit]


class SerpApiClient:
    """Thin client with an optional on-disk cache so repeat runs cost nothing."""

    def __init__(self, api_key: Optional[str] = None, cache_dir: Optional[str] = None,
                 session: Optional[requests.Session] = None, timeout: float = 30.0):
        self.api_key = get_api_key(api_key)
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.session = session or requests.Session()
        self.timeout = timeout
        self.calls_made = 0
        self.cache_hits = 0

    def _cache_path(self, params: Dict) -> Optional[Path]:
        if not self.cache_dir:
            return None
        public = {k: v for k, v in sorted(params.items()) if k != "api_key"}
        digest = hashlib.sha256(json.dumps(public, sort_keys=True).encode()).hexdigest()[:24]
        return self.cache_dir / f"serp-{digest}.json"

    def raw_search(self, query: str, gl: str = "us", hl: str = "en",
                   location: Optional[str] = None, start: int = 0) -> Dict:
        params = {"engine": "google", "q": query, "gl": gl, "hl": hl, "start": start}
        if location:
            params["location"] = location
        return self._call(params)

    def _call(self, params: Dict) -> Dict:
        cache_path = self._cache_path(params)
        if cache_path and cache_path.exists():
            self.cache_hits += 1
            return json.loads(cache_path.read_text())
        response = self.session.get(
            SERPAPI_ENDPOINT, params={**params, "api_key": self.api_key}, timeout=self.timeout
        )
        self.calls_made += 1
        try:
            payload = response.json()
        except ValueError as exc:
            raise SerpApiError(f"SerpApi returned non-JSON (HTTP {response.status_code})") from exc
        if response.status_code != 200 or payload.get("error"):
            raise SerpApiError(
                f"SerpApi request failed (HTTP {response.status_code}): {payload.get('error', 'unknown error')}"
            )
        if cache_path:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(payload))
        return payload

    def search(self, query: str, **kwargs) -> List[SearchResult]:
        return parse_organic_results(self.raw_search(query, **kwargs), query)

    def news_search(self, query: str, gl: str = "us", hl: str = "en") -> List[SearchResult]:
        return parse_news_results(self._call({"engine": "google_news", "q": query, "gl": gl, "hl": hl}), query)

    def trends_related(self, query: str, geo: str = "", date: str = "today 3-m") -> List[TrendQuery]:
        params = {"engine": "google_trends", "q": query, "data_type": "RELATED_QUERIES", "date": date}
        if geo:
            params["geo"] = geo.upper()
        return parse_trends_related(self._call(params))

    def search_with_related(self, query: str, **kwargs):
        payload = self.raw_search(query, **kwargs)
        return parse_organic_results(payload, query), parse_related_searches(payload)

"""The SlopRadar agent loop: plan queries, search, fetch, score, rank."""
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from .engine import score_text, band_for, SlopScore
from .extract import extract_text, extract_title
from .fetch import PageFetcher, FetchedPage
from .serp import SearchResult

QUERY_TEMPLATES = [
    "{niche}",
    "best {niche}",
    "{niche} guide",
    "how to choose {niche}",
    "{niche} tips",
    "what is {niche}",
]


def plan_queries(niche: str, count: int = 1) -> List[str]:
    """Deterministic query plan. More queries = wider sample of the niche = more credits."""
    niche = " ".join(niche.split())
    count = max(1, min(count, len(QUERY_TEMPLATES)))
    planned = []
    for template in QUERY_TEMPLATES:
        q = template.format(niche=niche)
        if q.lower() not in (p.lower() for p in planned):
            planned.append(q)
        if len(planned) == count:
            break
    return planned


_STOP = {"a", "an", "the", "for", "of", "to", "in", "on", "and", "or", "with", "best", "top", "free",
         "how", "what", "is", "are", "vs", "near", "me", "my", "your", "2024", "2025", "2026"}


def _tokens(text: str) -> set:
    return {t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t not in _STOP}


def on_topic(niche: str, candidates: List[str], min_overlap: float = 0.5) -> List[str]:
    """Keep follow-up queries that share at least half of the niche's content words.

    Google Trends "rising" lists often include unrelated breakout searches
    ("concerts", "soup" for "ai writing tools"). Those would drag unrelated pages
    into the index, so they are dropped here. Near-duplicates of the niche are
    dropped too, since they would return the same results.
    """
    core = _tokens(niche)
    if not core:
        return list(candidates)
    need = max(1, int(round(len(core) * min_overlap + 0.0001)))
    kept, seen = [], {frozenset(core)}
    for q in candidates:
        toks = _tokens(q)
        if len(core & toks) < need or frozenset(toks) in seen:
            continue
        seen.add(frozenset(toks))
        kept.append(q)
    return kept


def normalize_url(url: str) -> str:
    parts = urlparse(url)
    path = parts.path.rstrip("/") or "/"
    return urlunparse((parts.scheme.lower(), parts.netloc.lower().removeprefix("www."), path, "", "", ""))


@dataclass
class PageReport:
    rank: int
    query: str
    title: str
    url: str
    domain: str
    status: str
    score: Optional[int] = None
    band: str = ""
    word_count: int = 0
    density_per_1k: float = 0.0
    hits: List[Dict] = field(default_factory=list)
    category_totals: Dict[str, float] = field(default_factory=dict)
    error: str = ""

    def to_dict(self) -> Dict:
        return {
            "rank": self.rank, "query": self.query, "title": self.title, "url": self.url,
            "domain": self.domain, "status": self.status, "score": self.score, "band": self.band,
            "word_count": self.word_count, "density_per_1k": round(self.density_per_1k, 2),
            "category_totals": self.category_totals, "hits": self.hits, "error": self.error,
        }


@dataclass
class NicheReport:
    niche: str
    queries: List[str]
    pages: List[PageReport]
    slop_index: Optional[int]
    rank_weighted_index: Optional[int]
    band: str
    band_counts: Dict[str, int]
    top_rules: List[Dict]
    serp_calls: int
    serp_cache_hits: int
    elapsed_seconds: float
    generated_at: str

    def to_dict(self) -> Dict:
        return {
            "niche": self.niche,
            "queries": self.queries,
            "slop_index": self.slop_index,
            "rank_weighted_index": self.rank_weighted_index,
            "band": self.band,
            "band_counts": self.band_counts,
            "top_rules": self.top_rules,
            "serp_calls": self.serp_calls,
            "serp_cache_hits": self.serp_cache_hits,
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "generated_at": self.generated_at,
            "pages": [p.to_dict() for p in self.pages],
        }


def _score_page(result: SearchResult, rank: int, page: FetchedPage) -> PageReport:
    domain = urlparse(result.link).netloc.lower().removeprefix("www.")
    base = PageReport(rank=rank, query=result.query, title=result.title, url=result.link,
                      domain=domain, status="error")
    if not page.ok:
        base.error = page.error
        base.band = "Not scored"
        return base
    text = extract_text(page.html)
    title = result.title or extract_title(page.html) or result.link
    scored: SlopScore = score_text(text)
    base.title = title
    base.status = "scored" if scored.score is not None else "too-little-text"
    base.score = scored.score
    base.band = scored.band
    base.word_count = scored.word_count
    base.density_per_1k = scored.density_per_1k
    base.hits = [h.to_dict() for h in scored.hits]
    base.category_totals = {k: round(v, 2) for k, v in scored.category_totals.items()}
    return base


def build_index(pages: List[PageReport]):
    scored = [p for p in pages if p.score is not None]
    if not scored:
        return None, None
    plain = int(round(statistics.mean(p.score for p in scored)))
    # Rank weighting: position 1 counts most, since that is what searchers read.
    weights = [1.0 / p.rank for p in scored]
    weighted = int(round(sum(p.score * w for p, w in zip(scored, weights)) / sum(weights)))
    return plain, weighted


def top_rules(pages: List[PageReport], limit: int = 10) -> List[Dict]:
    tally: Dict[str, Dict] = {}
    for p in pages:
        for h in p.hits:
            entry = tally.setdefault(h["rule_id"], {
                "rule_id": h["rule_id"], "description": h["description"], "category": h["category"],
                "total_hits": 0, "pages": 0,
            })
            entry["total_hits"] += h["count"]
            entry["pages"] += 1
    return sorted(tally.values(), key=lambda e: (-e["pages"], -e["total_hits"], e["rule_id"]))[:limit]


def run_radar(niche: str, search: Callable[[str], List[SearchResult]], fetcher: PageFetcher,
              queries: int = 1, max_results: int = 10,
              progress: Optional[Callable[[str], None]] = None,
              serp_stats: Optional[Callable[[], Dict[str, int]]] = None,
              related_search: Optional[Callable[[str], Tuple[List[SearchResult], List[str]]]] = None
              ) -> NicheReport:
    """Plan, search, dedupe, fetch, score and aggregate.

    With ``related_search`` the planner is driven by SerpApi itself: the first
    search runs on the niche, and follow-up queries come from Google's related
    searches / people-also-ask for that niche. Otherwise fixed templates are used.
    """
    started = time.time()
    say = progress or (lambda msg: None)
    results_by_query: Dict[str, List[SearchResult]] = {}
    if related_search and queries > 1:
        first = " ".join(niche.split())
        first_results, related = related_search(first)
        results_by_query[first] = first_results
        plan = [first] + [q for q in related if q.lower() != first.lower()][: queries - 1]
        if len(plan) < queries:  # Google offered too few; top up with templates
            plan += [q for q in plan_queries(niche, 6) if q not in plan][: queries - len(plan)]
        say(f"SerpApi suggested follow-ups: {', '.join(plan[1:]) or 'none'}")
    else:
        plan = plan_queries(niche, queries)
    say(f"Planned {len(plan)} quer{'y' if len(plan) == 1 else 'ies'}: {', '.join(plan)}")

    picked: List[SearchResult] = []
    seen = set()
    for q in plan:
        results = results_by_query[q] if q in results_by_query else search(q)
        say(f"SerpApi: {len(results)} organic results for '{q}'")
        for r in results:
            key = normalize_url(r.link)
            if key in seen:
                continue
            seen.add(key)
            picked.append(r)
    # Interleave by position across queries so each query's top results make the cut.
    picked.sort(key=lambda r: (r.position, plan.index(r.query)))
    picked = picked[:max_results]

    say(f"Fetching {len(picked)} pages...")
    pages = fetcher.fetch_many([r.link for r in picked])
    reports = [_score_page(r, i + 1, pages[r.link]) for i, r in enumerate(picked)]

    plain, weighted = build_index(reports)
    counts: Dict[str, int] = {}
    for p in reports:
        counts[p.band] = counts.get(p.band, 0) + 1
    stats = serp_stats() if serp_stats else {}
    return NicheReport(
        niche=niche,
        queries=plan,
        pages=reports,
        slop_index=plain,
        rank_weighted_index=weighted,
        band=band_for(plain),
        band_counts=counts,
        top_rules=top_rules(reports),
        serp_calls=stats.get("calls", 0),
        serp_cache_hits=stats.get("cache_hits", 0),
        elapsed_seconds=time.time() - started,
        generated_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )

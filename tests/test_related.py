from slopradar.fetch import FetchedPage, PageFetcher
from slopradar.pipeline import run_radar
from slopradar.serp import SearchResult, parse_related_searches


def test_parse_related_searches_merges_and_dedupes():
    payload = {
        "related_searches": [{"query": "best standing desk"}, {"query": "Best  Standing Desk"}, {"query": "standing desk india"}],
        "related_questions": [{"question": "Are standing desks worth it?"}, {"question": None}],
    }
    assert parse_related_searches(payload) == ["best standing desk", "standing desk india", "Are standing desks worth it?"]
    assert parse_related_searches(payload, limit=1) == ["best standing desk"]
    assert parse_related_searches({}) == []


class NoPages(PageFetcher):
    def __init__(self):
        super().__init__(respect_robots=False)

    def fetch(self, url):
        return FetchedPage(url=url, ok=False, error="offline")


def _r(q, n):
    return [SearchResult(query=q, position=i + 1, title=f"{q} {i}", link=f"https://{abs(hash(q)) % 999}.example.com/{i}") for i in range(n)]


def test_related_expansion_uses_google_suggestions_and_does_not_research_first_query():
    calls = []

    def search(q):
        calls.append(q)
        return _r(q, 3)

    def related(q):
        calls.append("related:" + q)
        return _r(q, 3), ["standing desks", "standing desk for back pain", "cheap standing desk"]

    report = run_radar("standing desks", search=search, fetcher=NoPages(), queries=3, related_search=related)
    assert report.queries == ["standing desks", "standing desk for back pain", "cheap standing desk"]
    assert calls == ["related:standing desks", "standing desk for back pain", "cheap standing desk"]


def test_related_expansion_tops_up_with_templates():
    report = run_radar("desks", search=lambda q: _r(q, 1), fetcher=NoPages(), queries=3,
                       related_search=lambda q: (_r(q, 1), []))
    assert report.queries == ["desks", "best desks", "desks guide"]


def test_single_query_ignores_related():
    called = []
    run_radar("desks", search=lambda q: _r(q, 1), fetcher=NoPages(), queries=1,
              related_search=lambda q: called.append(q) or (_r(q, 1), ["x"]))
    assert called == []

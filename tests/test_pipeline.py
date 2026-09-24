from slopradar.fetch import FetchedPage, PageFetcher
from slopradar.pipeline import plan_queries, normalize_url, run_radar, build_index, PageReport
from slopradar.serp import parse_organic_results


class DictFetcher(PageFetcher):
    def __init__(self, pages):
        super().__init__(respect_robots=False)
        self.pages = pages

    def fetch(self, url):
        html = self.pages.get(url)
        if html is None:
            return FetchedPage(url=url, ok=False, status=404, error="HTTP 404")
        return FetchedPage(url=url, ok=True, status=200, html=html)


def test_plan_queries_is_deterministic_and_bounded():
    assert plan_queries("standing desks", 1) == ["standing desks"]
    assert plan_queries("  standing   desks ", 3) == ["standing desks", "best standing desks", "standing desks guide"]
    assert len(plan_queries("x", 99)) == 6
    assert plan_queries("x", 0) == ["x"]


def test_normalize_url_dedupes_variants():
    assert normalize_url("https://www.Example.com/a/?utm=1#x") == normalize_url("https://example.com/a")


def _run(serp_payload, slop_html, human_html, **kw):
    pages = {"https://slop.example.com/guide": slop_html, "https://www.human.example.com/review/": human_html}
    return run_radar("standing desks", search=lambda q: parse_organic_results(serp_payload, q),
                     fetcher=DictFetcher(pages), **kw)


def test_run_radar_end_to_end(serp_payload, slop_html, human_html):
    report = _run(serp_payload, slop_html, human_html)
    # duplicate of the human review is removed, broken page kept but unscored
    urls = [p.url for p in report.pages]
    assert "https://human.example.com/review" not in urls
    assert len(report.pages) == 3
    first = report.pages[0]
    assert first.rank == 1 and first.domain == "slop.example.com" and first.band == "Slop"
    assert first.hits and all("rule_id" in h and h["examples"] for h in first.hits)
    broken = [p for p in report.pages if p.domain == "broken.example.com"][0]
    assert broken.score is None and broken.error == "HTTP 404"
    assert report.slop_index is not None and 0 <= report.slop_index <= 100
    assert report.top_rules and report.top_rules[0]["pages"] >= 1


def test_max_results_limits_pages(serp_payload, slop_html, human_html):
    report = _run(serp_payload, slop_html, human_html, max_results=1)
    assert len(report.pages) == 1


def test_multiple_queries_each_searched(serp_payload, slop_html, human_html):
    seen = []

    def search(q):
        seen.append(q)
        return parse_organic_results(serp_payload, q)

    run_radar("standing desks", search=search, fetcher=DictFetcher({}), queries=3)
    assert seen == ["standing desks", "best standing desks", "standing desks guide"]


def test_index_math():
    pages = [PageReport(rank=1, query="q", title="", url="", domain="", status="scored", score=90),
             PageReport(rank=2, query="q", title="", url="", domain="", status="scored", score=30),
             PageReport(rank=3, query="q", title="", url="", domain="", status="error", score=None)]
    plain, weighted = build_index(pages)
    assert plain == 60
    assert weighted == 70  # (90*1 + 30*0.5) / 1.5
    assert build_index([]) == (None, None)

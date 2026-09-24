import json

import slopradar.cli as cli
from slopradar.fetch import FetchedPage
from slopradar.serp import SearchResult, SerpApiError, TrendQuery

SLOP = "<p>" + "In today's fast-paced world, let's dive in and unlock the power of synergy. " * 30 + "</p>"
PLAIN = "<p>" + "The council voted 7 to 2 on Tuesday to repave Main Street next spring. " * 30 + "</p>"


class FakeClient:
    trends_fail = False

    def __init__(self, cache_dir=None):
        self.calls_made = 0
        self.cache_hits = 0
        self.log = []

    def search(self, q, gl="us", hl="en", location=None):
        self.calls_made += 1
        self.log.append(("web", q))
        return [SearchResult(query=q, position=1, title="Web " + q, link=f"https://web.example.com/{abs(hash(q))}")]

    def news_search(self, q, gl="us", hl="en"):
        self.calls_made += 1
        self.log.append(("news", q))
        return [SearchResult(query=q, position=1, title="News", link="https://news.example.com/a")]

    def trends_related(self, q, geo="", date="today 3-m"):
        self.calls_made += 1
        self.log.append(("trends", q))
        if self.trends_fail:
            raise SerpApiError("no data")
        return [TrendQuery("ai tools rising one", "rising", "Breakout", 5000), TrendQuery("concerts", "rising", "+900%", 900), TrendQuery("ai tools rising two", "rising", "+300%", 300)]


def _fetch(self, url):
    return FetchedPage(url=url, ok=True, status=200, html=PLAIN if "news" in url else SLOP)


def test_channels_compares_web_and_news(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SerpApiClient", FakeClient)
    monkeypatch.setattr(cli.PageFetcher, "fetch", _fetch)
    assert cli.main(["channels", "city budget", "--quiet"]) == 0
    out = capsys.readouterr().out
    assert "web pages read sloppier" in out
    assert "SerpApi calls: 2" in out


def test_channels_json(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SerpApiClient", FakeClient)
    monkeypatch.setattr(cli.PageFetcher, "fetch", _fetch)
    assert cli.main(["channels", "x", "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data["channels"]) == {"web", "news"}
    assert data["channels"]["web"]["slop_index"] > data["channels"]["news"]["slop_index"]


def test_scan_expand_trends_uses_rising_queries(monkeypatch, capsys):
    made = []

    class Tracking(FakeClient):
        def __init__(self, cache_dir=None):
            super().__init__(cache_dir)
            made.append(self)

    monkeypatch.setattr(cli, "SerpApiClient", Tracking)
    monkeypatch.setattr(cli.PageFetcher, "fetch", _fetch)
    assert cli.main(["scan", "ai tools", "--queries", "3", "--expand", "trends", "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["queries"] == ["ai tools", "ai tools rising one", "ai tools rising two"]  # "concerts" dropped
    assert made[0].log[:2] == [("web", "ai tools"), ("trends", "ai tools")]


def test_scan_expand_trends_falls_back_when_trends_empty(monkeypatch, capsys):
    class Failing(FakeClient):
        trends_fail = True

    monkeypatch.setattr(cli, "SerpApiClient", Failing)
    monkeypatch.setattr(cli.PageFetcher, "fetch", _fetch)
    assert cli.main(["scan", "ai tools", "--queries", "2", "--expand", "trends", "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["queries"] == ["ai tools", "best ai tools"]

import json

import slopradar.cli as cli
from slopradar.fetch import FetchedPage
from slopradar.serp import SearchResult

SLOP = "<p>" + "In today's fast-paced world, let's dive in and unlock the power of synergy. " * 30 + "</p>"
PLAIN = "<p>" + "The desk arrived on Tuesday and the box was heavy to carry upstairs. " * 30 + "</p>"


class FakeClient:
    def __init__(self, cache_dir=None):
        self.calls_made = 0
        self.cache_hits = 0
        self.seen = []

    def search(self, q, gl="us", hl="en"):
        self.calls_made += 1
        self.seen.append(gl)
        return [SearchResult(query=q, position=1, title="Shared", link="https://shared.example.com/"),
                SearchResult(query=q, position=2, title=gl, link=f"https://{gl}.example.com/")]


def test_compare_ranks_markets(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SerpApiClient", FakeClient)
    pages = {"https://shared.example.com/": PLAIN, "https://us.example.com/": SLOP, "https://in.example.com/": PLAIN}
    monkeypatch.setattr(cli.PageFetcher, "fetch",
                        lambda self, url: FetchedPage(url=url, ok=True, status=200, html=pages[url]))
    assert cli.main(["compare", "desks", "--quiet"]) == 0
    out = capsys.readouterr().out
    lines = [l for l in out.splitlines() if "gl=" in l]
    assert lines[0].strip().startswith("gl=us")  # sloppier market listed first
    assert "shared.example.com" in out
    assert "SerpApi calls: 2" in out


def test_compare_json_and_custom_markets(monkeypatch, capsys):
    monkeypatch.setattr(cli, "SerpApiClient", FakeClient)
    monkeypatch.setattr(cli.PageFetcher, "fetch",
                        lambda self, url: FetchedPage(url=url, ok=True, status=200, html=PLAIN))
    assert cli.main(["compare", "desks", "--gl", "uk", "--gl", "au", "--gl", "in", "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert list(data["markets"]) == ["uk", "au", "in"]


def test_compare_needs_two_markets(capsys):
    assert cli.main(["compare", "desks", "--gl", "us", "--quiet"]) == 2

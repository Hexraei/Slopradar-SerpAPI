import pytest

from slopradar.serp import (SerpApiClient, SerpApiError, parse_news_results, parse_trends_related)
from tests.test_serp import FakeSession

NEWS = {
    "news_results": [
        {"position": 1, "title": "Flat story", "link": "https://news-a.example.com/1",
         "source": {"name": "Paper A"}, "date": "09/24/2026"},
        {"position": 2, "title": "Cluster", "stories": [
            {"title": "Inner 1", "link": "https://news-b.example.com/2", "source": {"name": "Paper B"}},
            {"title": "Inner 2", "link": "https://news-c.example.com/3", "source": {"name": "Paper C"}},
        ]},
        {"position": 3, "title": "No link"},
    ]
}

TRENDS = {
    "related_queries": {
        "rising": [
            {"query": "ai humanizer", "value": "+450%", "extracted_value": 450},
            {"query": "ai detector free", "value": "Breakout", "extracted_value": 5000},
        ],
        "top": [
            {"query": "AI Humanizer", "value": "100", "extracted_value": 100},
            {"query": "chatgpt", "value": "80", "extracted_value": 80},
        ],
    }
}


def test_news_flattens_clusters_and_ranks_in_order():
    results = parse_news_results(NEWS, "q")
    assert [r.link for r in results] == ["https://news-a.example.com/1", "https://news-b.example.com/2",
                                         "https://news-c.example.com/3"]
    assert [r.position for r in results] == [1, 2, 3]
    assert results[1].source == "Paper B"


def test_trends_rising_first_strongest_first_deduped():
    trends = parse_trends_related(TRENDS)
    assert [t.query for t in trends] == ["ai detector free", "ai humanizer", "chatgpt"]
    assert trends[0].kind == "rising" and trends[0].value == "Breakout"
    assert trends[-1].kind == "top"
    assert len(parse_trends_related(TRENDS, limit=1)) == 1
    assert parse_trends_related({}) == []


def test_trends_error_raises():
    with pytest.raises(SerpApiError):
        parse_trends_related({"error": "Google Trends hasn't returned any results for this query."})


def test_client_uses_right_engines():
    s = FakeSession(NEWS)
    c = SerpApiClient(api_key="k", session=s)
    c.news_search("ai tools", gl="in")
    assert s.calls[0][1]["engine"] == "google_news" and s.calls[0][1]["gl"] == "in"
    s2 = FakeSession(TRENDS)
    c2 = SerpApiClient(api_key="k", session=s2)
    c2.trends_related("ai tools", geo="in")
    p = s2.calls[0][1]
    assert p["engine"] == "google_trends" and p["data_type"] == "RELATED_QUERIES" and p["geo"] == "IN"


def test_on_topic_filter_on_real_trends_response():
    # Recorded Google Trends RELATED_QUERIES response (US, past 90 days, Sep 2026).
    import json
    from pathlib import Path
    from slopradar.pipeline import on_topic
    payload = json.loads((Path(__file__).parent / "fixtures" / "trends_ai_writing_tools.json").read_text())
    trends = [t.query for t in parse_trends_related(payload, limit=50)]
    assert "concerts" in trends and "soup" in trends
    kept = on_topic("ai writing tools", trends)
    assert "concerts" not in kept and "soup" not in kept and "best data visualization tools" not in kept
    assert kept[0] == "ai content writing tools"
    assert "ai tools for writing" not in kept  # same words as the niche, would repeat its results
    assert "ai tools for academic writing" in kept

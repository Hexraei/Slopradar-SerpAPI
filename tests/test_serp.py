import json

import pytest

from slopradar.serp import SerpApiClient, SerpApiError, parse_organic_results, get_api_key, ENV_KEY


class FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status_code = status

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params)))
        return FakeResponse(self.payload, self.status)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv(ENV_KEY, raising=False)
    with pytest.raises(SerpApiError, match=ENV_KEY):
        get_api_key()


def test_key_from_env(monkeypatch):
    monkeypatch.setenv(ENV_KEY, "abc123")
    assert get_api_key() == "abc123"


def test_parse_skips_ads_and_non_http_and_sorts(serp_payload):
    results = parse_organic_results(serp_payload, "standing desks")
    assert [r.position for r in results] == [1, 2, 3, 4]
    assert all(r.link.startswith("http") for r in results)
    assert not any("ads.example.com" in r.link for r in results)
    assert results[1].source == "Human Blog"


def test_parse_raises_on_error_payload():
    with pytest.raises(SerpApiError, match="Invalid API key"):
        parse_organic_results({"error": "Invalid API key."}, "q")


def test_client_sends_expected_params(monkeypatch, serp_payload):
    session = FakeSession(serp_payload)
    client = SerpApiClient(api_key="k", session=session)
    results = client.search("standing desks", gl="in", hl="en", location="Chennai, Tamil Nadu, India")
    url, params = session.calls[0]
    assert url == "https://serpapi.com/search.json"
    assert params["engine"] == "google" and params["q"] == "standing desks"
    assert params["gl"] == "in" and params["location"].startswith("Chennai")
    assert params["api_key"] == "k"
    assert len(results) == 4 and client.calls_made == 1


def test_client_http_error_is_clear():
    client = SerpApiClient(api_key="k", session=FakeSession({"error": "Your account has run out of searches."}, 429))
    with pytest.raises(SerpApiError, match="HTTP 429"):
        client.search("x")


def test_cache_avoids_second_call_and_never_stores_key(tmp_path, serp_payload):
    session = FakeSession(serp_payload)
    client = SerpApiClient(api_key="secret-key", session=session, cache_dir=str(tmp_path))
    client.search("standing desks")
    client.search("standing desks")
    assert len(session.calls) == 1 and client.cache_hits == 1
    for f in tmp_path.iterdir():
        assert "secret-key" not in f.read_text() and "secret-key" not in f.name

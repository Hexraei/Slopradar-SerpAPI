import json

from slopradar.cli import main
from slopradar.serp import ENV_KEY


def test_demo_runs_offline(capsys, tmp_path):
    md = tmp_path / "r.md"
    assert main(["demo", "--quiet", "--markdown", str(md)]) == 0
    out = capsys.readouterr().out
    assert "AI SLOP INDEX" in out and "No LLM" in out
    assert "# AI Slop Index: ai writing tools" in md.read_text()


def test_demo_json(capsys):
    assert main(["demo", "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["niche"] == "ai writing tools"
    assert data["pages"][0]["hits"]
    assert data["serp_calls"] == 0


def test_scan_without_key_fails_cleanly(monkeypatch, capsys):
    monkeypatch.delenv(ENV_KEY, raising=False)
    assert main(["scan", "anything", "--quiet"]) == 2
    assert ENV_KEY in capsys.readouterr().err


def test_scan_replays_saved_serp_json(tmp_path, capsys, monkeypatch):
    import slopradar.cli as cli
    from slopradar.fetch import FetchedPage

    serp = {"organic_results": [{"position": 1, "title": "T", "link": "https://x.example.com/"}]}
    f = tmp_path / "serp.json"
    f.write_text(json.dumps(serp))
    body = "<p>" + "In today's fast-paced world, let's dive in. " * 40 + "</p>"
    monkeypatch.setattr(cli.PageFetcher, "fetch", lambda self, url: FetchedPage(url=url, ok=True, status=200, html=body))
    assert main(["scan", "x", "--serp-json", str(f), "--quiet", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["pages"][0]["band"] == "Slop"


def test_score_file_and_rules(tmp_path, capsys):
    f = tmp_path / "copy.txt"
    f.write_text("Let's dive in. " + "The desk arrived on Tuesday. " * 30)
    assert main(["score", str(f)]) == 0
    assert "phrase.let-s-dive-in" in capsys.readouterr().out
    assert main(["rules"]) == 0
    assert "rules in" in capsys.readouterr().out


def test_bad_cli_inputs_are_clean_errors(capsys):
    for argv in [["demo", "--num", "-1"], ["scan", "x", "--queries", "7"],
                 ["scan", " "], ["score", "/file-that-does-not-exist"],
                 ["demo", "--show-rules", "-1"]]:
        assert main(argv) == 2
        assert "error:" in capsys.readouterr().err


def test_demo_provenance_and_coverage(capsys):
    assert main(["demo", "--json", "--quiet"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["source_mode"] == "demo"
    assert data["coverage"] == {"selected": 5, "scored": 4, "percent": 80.0}
    assert data["warnings"]

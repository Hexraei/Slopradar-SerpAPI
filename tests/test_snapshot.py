import json
import pytest
from slopradar.snapshot import compare_snapshots
from slopradar.cli import main


def report(pages, index=50):
    return {"niche": "desks", "pages": pages, "slop_index": index}


def page(url, score):
    return {"url": url, "score": score}


def test_changes_keep_page_deltas_separate_from_turnover():
    before = report([page("https://x.test/a?utm_source=x", 80), page("https://x.test/old", 20)])
    after = report([page("https://x.test/a", 40), page("https://x.test/new", 90)], 65)
    result = compare_snapshots(before, after)
    assert result["index_delta"] == 15
    assert result["common_pages"][0]["delta"] == -40
    assert result["added_urls"] == ["https://x.test/new"]
    assert result["removed_urls"] == ["https://x.test/old"]
    assert "coverage" in result["warning"]


def test_unscored_page_never_becomes_a_zero_delta():
    result = compare_snapshots(report([page("https://x.test", None)]), report([page("https://x.test", 0)]))
    assert result["common_pages"][0]["delta"] is None


def test_wrong_niche_is_rejected():
    with pytest.raises(ValueError, match="same niche"):
        compare_snapshots(report([]), {"niche": "shoes", "pages": []})


def test_changes_cli_uses_saved_files(tmp_path, capsys):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(report([page("https://x.test", 80)])))
    b.write_text(json.dumps(report([page("https://x.test", 30)])))
    assert main(["changes", str(a), str(b), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["common_pages"][0]["delta"] == -50


def test_demo_and_live_reports_are_not_comparable():
    a, b = report([]), report([])
    a["source_mode"], b["source_mode"] = "demo", "live"
    with pytest.raises(ValueError, match="source mode"):
        compare_snapshots(a, b)


def test_different_query_plans_are_not_comparable():
    a, b = report([]), report([])
    a["queries"], b["queries"] = ["desks"], ["desks", "best desks"]
    with pytest.raises(ValueError, match="query plan"):
        compare_snapshots(a, b)

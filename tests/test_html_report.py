from slopradar.cli import main


def test_html_report_is_self_contained_and_escaped(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["demo", "--quiet", "--html", str(out)]) == 0
    page = out.read_text()
    assert page.startswith("<!doctype html>")
    assert "AI Slop Index: ai writing tools" in page
    assert "<script" not in page and "http://" not in page.replace("https://", "")
    assert "structure.em-dash" in page
    # quotes from page text must be escaped, never raw HTML
    assert "&quot;" in page or "&#x27;" in page


def test_demo_report_does_not_claim_live_data(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["demo", "--quiet", "--html", str(out)]) == 0
    page = out.read_text()
    assert "Offline demo / sample data" in page and "Live search / SerpApi" not in page
    assert "not authorship detection" in page


def test_report_has_no_decorative_badges_or_external_scripts(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["demo", "--quiet", "--html", str(out)]) == 0
    page = out.read_text()
    assert "#5b21f5" not in page and "gradient" not in page and 'class="band"' not in page
    assert "Pages in search order" in page and "View evidence" in page
    assert "weighted points" in page and "80 readable words" in page
    assert "<script" not in page

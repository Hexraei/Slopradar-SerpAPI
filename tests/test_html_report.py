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

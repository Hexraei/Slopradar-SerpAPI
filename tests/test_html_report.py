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
    assert "The result ledger" in page and "Read evidence" in page
    assert "weighted points" in page and "80 readable words" in page
    assert "<script" not in page


def test_report_embeds_distinctive_fonts_without_remote_requests(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["demo", "--quiet", "--html", str(out)]) == 0
    page = out.read_text()
    assert "data:font/woff2;base64," in page and "Newsreader" in page and "IBM Plex Sans" in page
    assert "fonts.googleapis.com" not in page


def test_fingerprint_maps_real_scores_and_missing_pages(tmp_path, capsys):
    out = tmp_path / "r.html"
    assert main(["demo", "--quiet", "--html", str(out)]) == 0
    page = out.read_text()
    assert 'viewBox="0 0 1100 406"' in page
    assert 'viewBox="0 0 380 356"' in page
    assert "Search fingerprint" in page and "unscored, not zero" in page
    assert 'href="#case-1"' in page and 'id="case-1"' in page
    assert "FOUND IN RESULT 01" in page
    assert 'stroke-width="2"' in page


def test_live_report_embeds_sponsor_wordmark_and_nonredundant_copy():
    from slopradar.pipeline import NicheReport
    from slopradar.html_report import to_html
    report = NicheReport('test', ['test'], [], None, None, 'Not scored', {}, [], 1, 0, 0, '2026-10-05', 'live')
    page = to_html(report)
    assert 'Live search using' in page and 'data:image/svg+xml;base64,' in page
    assert 'alt="SerpApi"' in page
    assert 'Writing audit / evidence atlas' not in page
    assert 'A writing-pattern audit of the pages that rank for this search.' in page
    assert 'Each line is one ranked page. Longer line means a higher pattern score.' in page
    assert 'No scored pages' in page and 'n/a<span class=denom>' not in page

from slopradar.extract import extract_text, extract_title


def test_drops_scripts_nav_footer_and_cookie_banners():
    html = """<html><head><title> My  Page </title><style>p{}</style></head><body>
    <nav>Home About Contact</nav><script>var x = 'Unlock the power';</script>
    <p>Real paragraph one.</p><div class="cookie-consent"><p>We use cookies</p></div>
    <p>Real paragraph two.</p><footer>Copyright</footer></body></html>"""
    text = extract_text(html)
    assert "Real paragraph one." in text and "Real paragraph two." in text
    for noise in ("Home About", "Unlock", "cookies", "Copyright"):
        assert noise not in text
    assert extract_title(html) == "My Page"


def test_prefers_article_when_long_enough():
    body = "word " * 150
    html = f"<body><div>Sidebar junk here</div><article><p>{body}</p></article></body>"
    text = extract_text(html)
    assert "Sidebar" not in text


def test_falls_back_to_whole_page_when_article_is_short():
    html = "<body><p>Outside text.</p><article><p>Tiny.</p></article></body>"
    text = extract_text(html)
    assert "Outside text." in text and "Tiny." in text


def test_tolerates_broken_html():
    html = "<body><p>Unclosed <b>bold<p>Next para</div></span>"
    assert "Next para" in extract_text(html)


def test_hidden_content_is_not_reader_visible():
    html = '<main><div hidden>HIDDEN</div><p aria-hidden="true">HIDDEN</p><span style="display: none">HIDDEN</span><p>Real story.</p></main>'
    assert extract_text(html) == "Real story."


def test_noise_hints_do_not_drop_shared_article_or_commentary():
    assert extract_text('<div class="shared-article"><p>Real story.</p></div>') == "Real story."
    assert extract_text('<div class="commentary"><p>Analysis.</p></div>') == "Analysis."


def test_self_closing_skip_tag_does_not_swallow_article():
    assert extract_text('<script/><p>Real story.</p>') == "Real story."


def test_valueless_hidden_attributes_do_not_crash():
    text = extract_text('<article aria-hidden style><p>Visible evidence stays readable.</p></article>')
    assert 'Visible evidence stays readable.' in text

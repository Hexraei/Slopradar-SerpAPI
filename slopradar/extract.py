"""Turn a web page into the copy a reader actually sees.

Standard library only. Drops scripts, styles, navigation, headers, footers,
forms and cookie banners, and prefers <main>/<article> when a page has one.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from typing import List, Optional

SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "header", "footer", "aside",
             "form", "button", "select", "option", "template", "iframe", "canvas"}
BLOCK_TAGS = {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "td", "th",
              "dd", "dt", "figcaption", "summary", "pre", "div", "section", "article", "br"}
VOID_TAGS = {"br", "img", "hr", "meta", "link", "input", "source", "area", "base", "col",
             "embed", "param", "track", "wbr"}
NOISE_HINTS = re.compile(r"cookie|consent|newsletter|subscribe|popup|modal|share|social|breadcrumb|comment",
                         re.IGNORECASE)


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: List[str] = []
        self.skip_depth = 0
        self.main_depth = 0
        self.all_blocks: List[str] = []
        self.main_blocks: List[str] = []
        self.buffer: List[str] = []
        self.title = ""
        self._in_title = False

    def _flush(self) -> None:
        text = re.sub(r"\s+", " ", "".join(self.buffer)).strip()
        self.buffer = []
        if text:
            self.all_blocks.append(text)
            if self.main_depth:
                self.main_blocks.append(text)

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._in_title = True
        if tag in VOID_TAGS:
            if tag == "br":
                self._flush()
            return
        attr_text = " ".join(v or "" for k, v in attrs if k in ("class", "id", "role"))
        noisy = bool(attr_text and NOISE_HINTS.search(attr_text)) and tag in ("div", "section", "aside", "ul")
        self.stack.append(tag)
        if self.skip_depth or tag in SKIP_TAGS or noisy:
            self.skip_depth += 1
            return
        if tag in ("main", "article"):
            self.main_depth += 1
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID_TAGS or tag not in self.stack:
            return
        # Pop up to and including the matching tag (tolerates sloppy HTML).
        while self.stack:
            top = self.stack.pop()
            if self.skip_depth:
                self.skip_depth -= 1
            else:
                if top in BLOCK_TAGS:
                    self._flush()
                if top in ("main", "article") and self.main_depth:
                    self._flush()
                    self.main_depth -= 1
            if top == tag:
                break

    def handle_data(self, data):
        if self._in_title:
            self.title += data
            return
        if not self.skip_depth:
            self.buffer.append(data)

    def close(self):
        super().close()
        self._flush()


def extract_text(html: str, min_main_words: int = 120) -> str:
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    main = "\n".join(parser.main_blocks)
    if len(main.split()) >= min_main_words:
        return main
    return "\n".join(parser.all_blocks)


def extract_title(html: str) -> Optional[str]:
    parser = _Extractor()
    parser.feed(html)
    parser.close()
    return re.sub(r"\s+", " ", parser.title).strip() or None

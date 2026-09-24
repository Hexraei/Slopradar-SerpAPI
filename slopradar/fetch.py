"""Fetch top-ranking pages politely: timeouts, size cap, robots.txt, HTML only."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from urllib import robotparser
from urllib.parse import urlparse

import requests

USER_AGENT = "SlopRadar/0.1 (+https://github.com/Hexraei/Slopradar-SerpAPI)"
# Many sites refuse bare bot user agents, so page requests look like a normal
# browser while still naming SlopRadar. robots.txt is checked against USER_AGENT.
BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 " + USER_AGENT),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_BYTES = 2_000_000


@dataclass
class FetchedPage:
    url: str
    ok: bool
    status: Optional[int] = None
    html: str = ""
    error: str = ""
    final_url: str = ""


class PageFetcher:
    def __init__(self, timeout: float = 12.0, respect_robots: bool = True,
                 session: Optional[requests.Session] = None, max_workers: int = 6):
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.session = session or requests.Session()
        self.session.headers.update(BROWSER_HEADERS)
        self.max_workers = max_workers
        self._robots: Dict[str, Optional[robotparser.RobotFileParser]] = {}

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = robotparser.RobotFileParser()
            try:
                resp = self.session.get(base + "/robots.txt", timeout=self.timeout)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                    self._robots[base] = rp
                else:
                    self._robots[base] = None  # no robots.txt means allowed
            except requests.RequestException:
                self._robots[base] = None
        rp = self._robots[base]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    def fetch(self, url: str) -> FetchedPage:
        if not self.allowed(url):
            return FetchedPage(url=url, ok=False, error="blocked by robots.txt")
        try:
            resp = self.session.get(url, timeout=self.timeout, stream=True, allow_redirects=True)
        except requests.RequestException as exc:
            return FetchedPage(url=url, ok=False, error=f"{type(exc).__name__}: {exc}"[:200])
        ctype = resp.headers.get("Content-Type", "")
        if resp.status_code >= 400:
            return FetchedPage(url=url, ok=False, status=resp.status_code, error=f"HTTP {resp.status_code}")
        if ctype and "html" not in ctype.lower():
            return FetchedPage(url=url, ok=False, status=resp.status_code, error=f"not HTML ({ctype.split(';')[0]})")
        body = b""
        for chunk in resp.iter_content(65536):
            body += chunk
            if len(body) > MAX_BYTES:
                break
        encoding = resp.encoding or "utf-8"
        if encoding.lower() == "iso-8859-1" and "charset" not in ctype.lower():
            encoding = "utf-8"
        html = body.decode(encoding, errors="replace")
        return FetchedPage(url=url, ok=True, status=resp.status_code, html=html, final_url=resp.url or url)

    def fetch_many(self, urls: List[str], progress: Optional[Callable[[str], None]] = None) -> Dict[str, FetchedPage]:
        results: Dict[str, FetchedPage] = {}

        def one(u: str) -> FetchedPage:
            page = self.fetch(u)
            if progress:
                progress(u)
            return page

        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            for url, page in zip(urls, pool.map(one, urls)):
                results[url] = page
        return results

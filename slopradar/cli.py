"""Command line interface: `slopradar scan|score|rules|demo`."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .engine import RULES, CATEGORIES, score_text
from .extract import extract_text
from .fetch import PageFetcher
from .pipeline import run_radar
from .report import to_json, to_markdown, to_terminal
from .serp import SerpApiClient, SerpApiError, parse_organic_results


def _progress(quiet: bool):
    def say(msg: str) -> None:
        if not quiet:
            print(f"[slopradar] {msg}", file=sys.stderr)
    return say


def _emit(report, args) -> None:
    if args.markdown:
        Path(args.markdown).write_text(to_markdown(report), encoding="utf-8")
        _progress(args.quiet)(f"Markdown report written to {args.markdown}")
    if args.html:
        from .html_report import to_html
        Path(args.html).write_text(to_html(report), encoding="utf-8")
        _progress(args.quiet)(f"HTML report written to {args.html}")
    if args.json_out:
        Path(args.json_out).write_text(to_json(report), encoding="utf-8")
        _progress(args.quiet)(f"JSON report written to {args.json_out}")
    print(to_json(report) if args.json else to_terminal(report, show_rules=args.show_rules))


def _expander(args, client, say):
    """Pick where follow-up queries come from when --queries > 1."""
    if args.expand == "templates":
        return None
    if args.expand == "related":
        return lambda q: client.search_with_related(q, gl=args.gl, hl=args.hl, location=args.location)

    def trends(q):
        results = client.search(q, gl=args.gl, hl=args.hl, location=args.location)
        try:
            rising = client.trends_related(q, geo=args.gl)
        except SerpApiError as exc:
            say(f"Google Trends had nothing for '{q}' ({exc}); falling back to templates")
            return results, []
        say("Google Trends: " + ", ".join(f"{t.query} ({t.value})" for t in rising[:5]))
        return results, [t.query for t in rising]
    return trends


def cmd_scan(args) -> int:
    say = _progress(args.quiet)
    if args.serp_json:
        saved = json.loads(Path(args.serp_json).read_text(encoding="utf-8"))
        say(f"Replaying saved SerpApi response from {args.serp_json} (no SerpApi call)")
        fetcher = PageFetcher(timeout=args.timeout, respect_robots=not args.ignore_robots)
        report = run_radar(args.niche, search=lambda q: parse_organic_results(saved, q),
                           fetcher=fetcher, queries=1, max_results=args.num, progress=say)
        _emit(report, args)
        return 0
    try:
        client = SerpApiClient(cache_dir=None if args.no_cache else args.cache_dir)
    except SerpApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    fetcher = PageFetcher(timeout=args.timeout, respect_robots=not args.ignore_robots)
    try:
        report = run_radar(
            args.niche,
            search=lambda q: client.search(q, gl=args.gl, hl=args.hl, location=args.location),
            fetcher=fetcher,
            queries=args.queries,
            max_results=args.num,
            progress=say,
            serp_stats=lambda: {"calls": client.calls_made, "cache_hits": client.cache_hits},
            related_search=_expander(args, client, say),
        )
    except SerpApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    _emit(report, args)
    return 0


def cmd_compare(args) -> int:
    """Same niche, several Google markets: where is search sloppier?"""
    say = _progress(args.quiet)
    markets = args.gl or ["us", "in"]
    if len(markets) < 2:
        print("error: give at least two --gl values", file=sys.stderr)
        return 2
    try:
        client = SerpApiClient(cache_dir=None if args.no_cache else args.cache_dir)
    except SerpApiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    fetcher = PageFetcher(timeout=args.timeout, respect_robots=not args.ignore_robots)
    rows = []
    for gl in markets:
        say(f"Market gl={gl}")
        try:
            report = run_radar(args.niche, search=lambda q, gl=gl: client.search(q, gl=gl, hl=args.hl),
                               fetcher=fetcher, queries=1, max_results=args.num, progress=say)
        except SerpApiError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        rows.append((gl, report))
    if args.json:
        print(json.dumps({"niche": args.niche, "markets": {gl: r.to_dict() for gl, r in rows}},
                         indent=2, ensure_ascii=False))
        return 0
    print(f"AI Slop Index for \"{args.niche}\" by Google market")
    for gl, r in sorted(rows, key=lambda x: -(x[1].slop_index or -1)):
        idx = "n/a" if r.slop_index is None else f"{r.slop_index:>3}/100"
        scored = sum(1 for p in r.pages if p.score is not None)
        top = r.top_rules[0]["rule_id"] if r.top_rules else "-"
        print(f"  gl={gl:<4} {idx}  {r.band:<8} {scored}/{len(r.pages)} pages scored, top pattern: {top}")
    shared = set.intersection(*[{p.domain for p in r.pages} for _, r in rows])
    print(f"Domains ranking in every market: {', '.join(sorted(shared)) or 'none'}")
    print(f"SerpApi calls: {client.calls_made} (cache hits: {client.cache_hits})")
    return 0


class _FixtureFetcher(PageFetcher):
    """Serves pages from the bundled demo folder instead of the network."""

    def __init__(self, folder: Path, mapping: dict):
        super().__init__(respect_robots=False)
        self.folder = folder
        self.mapping = mapping

    def fetch(self, url):
        from .fetch import FetchedPage
        name = self.mapping.get(url)
        if not name:
            return FetchedPage(url=url, ok=False, error="not in demo fixtures")
        return FetchedPage(url=url, ok=True, status=200, html=(self.folder / name).read_text(encoding="utf-8"))


def cmd_demo(args) -> int:
    folder = Path(__file__).parent / "demo_data"
    serp = json.loads((folder / "serp_response.json").read_text(encoding="utf-8"))
    mapping = json.loads((folder / "pages.json").read_text(encoding="utf-8"))
    niche = serp["search_parameters"]["q"]
    _progress(args.quiet)("Demo mode: bundled SerpApi response and pages, no network, no API key.")
    report = run_radar(niche, search=lambda q: parse_organic_results(serp, q),
                       fetcher=_FixtureFetcher(folder, mapping), queries=1,
                       max_results=args.num, progress=_progress(args.quiet))
    _emit(report, args)
    return 0


def cmd_score(args) -> int:
    target = args.target
    if target == "-":
        text = sys.stdin.read()
    elif target.startswith(("http://", "https://")):
        page = PageFetcher(respect_robots=not args.ignore_robots).fetch(target)
        if not page.ok:
            print(f"error: could not fetch {target}: {page.error}", file=sys.stderr)
            return 2
        text = extract_text(page.html)
    else:
        raw = Path(target).read_text(encoding="utf-8", errors="replace")
        text = extract_text(raw) if target.lower().endswith((".html", ".htm")) else raw
    result = score_text(text)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        return 0
    print(f"Slop score: {'n/a' if result.score is None else result.score}/100 ({result.band}), "
          f"{result.word_count} words, {result.density_per_1k:.1f} weighted hits per 1k words")
    for h in result.hits:
        print(f"  {h.rule_id:<42} x{h.count:<3} w={h.weight:<4} \"{h.examples[0] if h.examples else ''}\"")
    return 0


def cmd_rules(args) -> int:
    rules = [r for r in RULES if not args.category or r.category == args.category]
    if args.json:
        print(json.dumps([{"id": r.id, "category": r.category, "description": r.description,
                           "weight": r.weight, "pattern": r.pattern.pattern} for r in rules], indent=2))
        return 0
    print(f"{len(rules)} rules in {len(CATEGORIES)} categories")
    for cat in CATEGORIES:
        n = sum(1 for r in rules if r.category == cat)
        if n:
            print(f"  {cat:<22} {n}")
    if args.category or args.verbose:
        for r in rules:
            print(f"{r.id:<45} {r.weight:<4} {r.description}")
    return 0


def _add_output_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--num", type=int, default=10, help="pages to score (default 10)")
    p.add_argument("--json", action="store_true", help="print the full JSON report to stdout")
    p.add_argument("--json-out", metavar="FILE", help="also write the JSON report to FILE")
    p.add_argument("--markdown", metavar="FILE", help="also write a Markdown report to FILE")
    p.add_argument("--html", metavar="FILE", help="also write a self-contained HTML report to FILE")
    p.add_argument("--show-rules", type=int, default=3, help="matched rules shown per page in the terminal")
    p.add_argument("--quiet", action="store_true", help="hide progress messages")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="slopradar",
                                     description="AI Slop Index for any Google niche. SerpApi for search, deterministic rules for scoring.")
    parser.add_argument("--version", action="version", version=f"slopradar {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="search a niche live via SerpApi and score the top pages")
    scan.add_argument("niche", help='keyword or niche, e.g. "project management software"')
    scan.add_argument("--queries", type=int, default=1,
                      help="how many query variants to search (1-6, each costs one SerpApi search)")
    scan.add_argument("--expand", choices=["related", "trends", "templates"], default="related",
                      help="how extra queries are chosen when --queries > 1: Google's related searches "
                           "(default, free with the first search), Google Trends rising queries "
                           "(one extra search), or fixed templates")
    scan.add_argument("--gl", default="us", help="Google country code (default us)")
    scan.add_argument("--hl", default="en", help="Google language code (default en)")
    scan.add_argument("--location", help='optional SerpApi location, e.g. "Chennai, Tamil Nadu, India"')
    scan.add_argument("--cache-dir", default=os.environ.get("SLOPRADAR_CACHE", ".slopradar_cache"),
                      help="where SerpApi responses are cached (default .slopradar_cache)")
    scan.add_argument("--no-cache", action="store_true", help="always call SerpApi")
    scan.add_argument("--timeout", type=float, default=12.0, help="page fetch timeout in seconds")
    scan.add_argument("--ignore-robots", action="store_true", help="do not check robots.txt")
    scan.add_argument("--serp-json", metavar="FILE",
                      help="replay a saved SerpApi JSON response instead of searching (pages are still fetched live)")
    _add_output_flags(scan)
    scan.set_defaults(func=cmd_scan)

    compare = sub.add_parser("compare", help="compare one niche across Google markets (one search per market)")
    compare.add_argument("niche")
    compare.add_argument("--gl", action="append", help="country code, repeat for each market (default: us and in)")
    compare.add_argument("--hl", default="en")
    compare.add_argument("--num", type=int, default=10)
    compare.add_argument("--cache-dir", default=os.environ.get("SLOPRADAR_CACHE", ".slopradar_cache"))
    compare.add_argument("--no-cache", action="store_true")
    compare.add_argument("--timeout", type=float, default=12.0)
    compare.add_argument("--ignore-robots", action="store_true")
    compare.add_argument("--json", action="store_true")
    compare.add_argument("--quiet", action="store_true")
    compare.set_defaults(func=cmd_compare)

    demo = sub.add_parser("demo", help="run the full pipeline on bundled sample data (no key needed)")
    _add_output_flags(demo)
    demo.set_defaults(func=cmd_demo)

    score = sub.add_parser("score", help="score one URL, file, or stdin (-) without searching")
    score.add_argument("target")
    score.add_argument("--json", action="store_true")
    score.add_argument("--ignore-robots", action="store_true")
    score.set_defaults(func=cmd_score)

    rules = sub.add_parser("rules", help="list the rule library")
    rules.add_argument("--category")
    rules.add_argument("--verbose", "-v", action="store_true")
    rules.add_argument("--json", action="store_true")
    rules.set_defaults(func=cmd_rules)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

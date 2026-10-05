"""Portable, accessible report. No scripts, external fonts or tracking."""
from __future__ import annotations
import html
from typing import List
from urllib.parse import urlparse
from .pipeline import NicheReport

CSS = """
:root{--ink:#202422;--muted:#5c645f;--line:#dce2dd;--accent:#21634b;--paper:#fff;--soft:#f4f6f3}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
a{color:var(--accent);text-underline-offset:3px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
.wrap{max-width:1120px;margin:auto;padding:28px 40px 64px}.mast{display:flex;justify-content:space-between;gap:20px;align-items:center;padding-bottom:22px;border-bottom:1px solid var(--line)}.brand{font-size:18px;font-weight:700;letter-spacing:-.5px}.meta,.muted{color:var(--muted)}.meta{font-size:13px}h1{font-size:40px;line-height:1.12;letter-spacing:-1.4px;margin:8px 0 12px}h2{font-size:22px;line-height:1.25;letter-spacing:-.4px;margin:0}h3{font-size:16px;margin:0}.eyebrow{font-size:12px;font-weight:600;letter-spacing:1.4px;text-transform:uppercase;color:var(--muted)}.intro{margin:36px 0 28px}.intro p{max-width:670px;margin:0;color:var(--muted)}
.overview{display:grid;grid-template-columns:1.15fr 1fr;border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:24px 0 32px}.scoreblock{padding:26px 32px 26px 0;border-right:1px solid var(--line)}.number{font-size:72px;font-weight:650;letter-spacing:-4px;line-height:1.1;font-variant-numeric:tabular-nums}.denom{font-size:24px;color:var(--muted);letter-spacing:-.4px}.verdict{font-weight:600;margin:8px 0 18px}.scale{height:5px;background:var(--line);position:relative;margin-top:18px}.scale i{display:block;height:5px;background:var(--accent)}.scale-labels{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:8px}.facts{padding:28px 0 24px 32px}.facts dl{display:grid;grid-template-columns:1fr auto;gap:10px 16px;margin:0}.facts dt{color:var(--muted)}.facts dd{margin:0;font-weight:600;font-variant-numeric:tabular-nums}.context{font-size:13px;line-height:1.6;color:var(--muted);margin:20px 0 0}.sectionhead{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin:34px 0 18px}.sectionhead p{font-size:13px;color:var(--muted);margin:0}.columns,.result summary{display:grid;grid-template-columns:36px minmax(0,1fr) 86px 120px;gap:18px;align-items:start}.columns{font-size:12px;color:var(--muted);padding:0 0 12px;border-bottom:1px solid var(--line)}.right{text-align:right}.result{border-bottom:1px solid var(--line)}.result summary{padding:20px 0;cursor:pointer;list-style:none}.result summary::-webkit-details-marker{display:none}.rank{font-size:13px;color:var(--muted);padding-top:4px}.title{font-size:16px;font-weight:600;line-height:1.4}.domain{font-size:13px;color:var(--muted);margin-top:5px}.metric{text-align:right;font-size:21px;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.4}.assessment{text-align:right;font-size:13px;line-height:1.5;padding-top:4px}.openhint{display:block;color:var(--accent);font-size:12px;font-weight:600;margin-top:4px}.result[open] .openhint{color:var(--muted)}.detail{padding:0 0 24px 54px;max-width:100%}.detail-meta{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-bottom:18px}.rules{display:grid;gap:20px}.rule{border-left:2px solid var(--line);padding-left:18px}.rule-head{display:flex;justify-content:space-between;gap:16px}.rule-head p{margin:0;font-size:13px;color:var(--muted);white-space:nowrap}.rule code{display:block;font-size:11px;color:var(--muted);overflow-wrap:anywhere;margin:4px 0 10px}blockquote{margin:8px 0 0;font-size:14px;color:var(--ink)}.reason{font-size:14px;color:var(--muted);margin:8px 0}.patterns{display:grid;grid-template-columns:1fr 1fr;gap:0 32px}.pattern{padding:14px 0;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:18px}.pattern p{margin:0;font-size:14px}.pattern small{font-size:12px;color:var(--muted);display:block}.pattern-count{white-space:nowrap;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums}.method{background:var(--soft);padding:24px;margin-top:36px}.method p{font-size:14px;color:var(--muted);margin:10px 0}.method ul{padding-left:20px;font-size:14px;color:var(--muted)}.foot{font-size:12px;color:var(--muted);margin-top:28px}.empty{padding:20px 0;color:var(--muted)}
@media(max-width:650px){.wrap{padding:20px 20px 40px}.mast{align-items:start}.mast .meta{text-align:right;max-width:160px}h1{font-size:32px;letter-spacing:-1px}.intro{margin:22px 0 18px}.overview{grid-template-columns:1fr}.scoreblock{border-right:0;border-bottom:1px solid var(--line);padding:18px 0}.number{font-size:56px}.facts{padding:16px 0}.facts dl{font-size:14px;gap:6px 12px}.context{margin-top:12px}.intro p{font-size:14px;line-height:1.5}.verdict{margin:5px 0 10px}.scale{margin-top:10px}.overview{margin:18px 0 22px}.mast{padding-bottom:16px}.sectionhead{display:block}.sectionhead p{margin-top:6px}.columns{display:none}.result summary{grid-template-columns:24px minmax(0,1fr) 54px;gap:10px;padding:18px 0}.assessment{grid-column:2/4;text-align:left;display:flex;justify-content:space-between;padding-top:0;gap:10px}.title{font-size:15px}.domain{font-size:12px;overflow-wrap:anywhere}.metric{font-size:22px}.openhint{margin:0}.detail{padding-left:34px}.rule{padding-left:12px}.rule-head{display:block}.rule-head p{margin-top:4px;white-space:normal}.patterns{grid-template-columns:1fr}.method{padding:20px}.meta{font-size:12px}.scale-labels{font-size:11px}}
@media print{.wrap{padding:0}details{break-inside:avoid}.detail{display:block}summary{cursor:default}.openhint{display:none}}
"""


def _safe_url(url: str) -> str:
    return url if urlparse(url).scheme in {"http", "https"} else "#"


def to_html(report: NicheReport, max_rules: int = 25) -> str:
    e = html.escape
    scored = sum(p.score is not None for p in report.pages)
    idx = "n/a" if report.slop_index is None else str(report.slop_index)
    rank = "Not available" if report.rank_weighted_index is None else f"{report.rank_weighted_index}/100"
    mode = {"demo": "Offline demo / sample data", "replay": "Saved rankings / replay", "live": "Live search / SerpApi"}.get(report.source_mode, report.source_mode)
    out: List[str] = ["<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
        f"<title>AI Slop Index: {e(report.niche)}</title><style>{CSS}</style></head><body><main class=wrap>",
        f'<header class=mast><span class=brand>SlopRadar</span><span class=meta>{e(mode)}</span></header>',
        f'<section class=intro><span class=eyebrow>Search quality report</span><h1>{e(report.niche)}</h1><p>Which pages lean on stock writing patterns? Inspect the scores, then read the evidence.</p></section>',
        '<section class=overview aria-label="Score and sample coverage"><div class=scoreblock><div class=eyebrow>AI Slop Index</div>',
        f'<div class=number>{idx}' + ('<span class=denom> /100</span>' if report.slop_index is not None else '') + '</div>',
        f'<div class=verdict>{e(report.band) if report.slop_index is not None else "No pages could be scored"}</div>',
        f'<div class=scale aria-hidden=true><i style="width:{report.slop_index or 0}%"></i></div><div class=scale-labels><span>0 / fewer patterns</span><span>100 / more patterns</span></div></div>',
        f'<div class=facts><dl><dt>Pages scored</dt><dd>{scored} of {len(report.pages)}</dd><dt>Rank-weighted index</dt><dd>{rank}</dd><dt>Searches used</dt><dd>{report.serp_calls}</dd><dt>Cached searches</dt><dd>{report.serp_cache_hits}</dd></dl><p class=context>A style-pattern score, not the chance a page was written by AI. Top-ranked pages count more in the rank-weighted index.</p></div></section>',
        '<div class=sectionhead><h2>Pages in search order</h2><p>Open a page to inspect its matched patterns.</p></div>',
        '<div class=columns aria-hidden=true><span>Rank</span><span>Page</span><span class=right>Score</span><span class=right>Assessment</span></div>']
    if not report.pages:
        out.append('<p class=empty>No pages were returned. Try a more specific query or check the saved search response.</p>')
    for p in report.pages:
        score = "n/a" if p.score is None else str(p.score)
        status = p.band if p.score is not None else "Not scored"
        out.append(f'<details class=result><summary><span class=rank>{p.rank:02d}</span><span><span class=title>{e(p.title)}</span><span class=domain style="display:block">{e(p.domain)}</span></span><span class=metric>{score}</span><span class=assessment>{e(status)}<span class=openhint>View evidence</span></span></summary><div class=detail>')
        out.append(f'<div class=detail-meta><a href="{e(_safe_url(p.url))}" rel="noreferrer">Open source page</a><span>{p.word_count:,} words extracted</span><span>{p.density_per_1k:.1f} weighted hits /1k words</span></div>')
        if p.score is None:
            out.append(f'<p class=reason>{e(p.error) if p.error else "Fewer than 80 readable words. This page does not contribute to the index."}</p>')
        if p.hits:
            out.append('<div class=rules>')
            for h in p.hits[:max_rules]:
                counted = h.get('counted_hits', min(h['count'], 5))
                contribution = h.get('contribution', counted * h['weight'])
                out.append(f'<article class=rule><div class=rule-head><h3>{e(h["description"])}</h3><p>{h["count"]} found / {counted} counted / {contribution:g} weighted points</p></div><code>{e(h["rule_id"])}</code>')
                for ex in h['examples']:
                    out.append(f'<blockquote>{e(ex)}</blockquote>')
                out.append('</article>')
            if len(p.hits) > max_rules:
                out.append(f'<p class=reason>{len(p.hits) - max_rules} more matched rules are available in the JSON report.</p>')
            out.append('</div>')
        elif p.score is not None:
            out.append('<p class=reason>No patterns matched. This does not establish human authorship.</p>')
        out.append('</div></details>')
    if report.top_rules:
        out.append('<div class=sectionhead><h2>Patterns across this sample</h2><p>Ordered by pages affected, then total hits.</p></div><div class=patterns>')
        for r in report.top_rules:
            out.append(f'<div class=pattern><div><p>{e(r["description"])}</p><small>{e(r["rule_id"])}</small></div><span class=pattern-count>{r["pages"]} pages<br>{r["total_hits"]} hits</span></div>')
        out.append('</div>')
    out.append('<section class=method><h2>How to read this report</h2><p>Scores come from deterministic rules. Repeated hits for one rule are capped at 5, then weighted and normalized by text length. No LLM is used.</p><ul>')
    for warning in report.warnings:
        out.append(f'<li>{e(warning)}</li>')
    out.append('</ul><p>Search queries: ' + e(', '.join(report.queries)) + f'</p><p>Generated: {e(report.generated_at)}. Source: {e(mode)}.</p></section><footer class=foot>Made with <a href="https://github.com/Hexraei/Slopradar-SerpAPI">SlopRadar</a>. Search data from SerpApi. Scores describe writing patterns, not authorship.</footer></main></body></html>')
    return '\n'.join(out)

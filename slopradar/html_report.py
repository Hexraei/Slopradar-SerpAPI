"""Self-contained HTML report: one file, no JavaScript, no external assets."""
from __future__ import annotations

import html
from typing import List

from .pipeline import NicheReport

BAND_COLORS = {"Human": "#1f9d55", "Mixed": "#d69e2e", "Sloppy": "#dd6b20", "Slop": "#c53030"}

CSS = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:980px;margin:32px auto;padding:0 16px;color:#1a1a2e}
h1{margin-bottom:4px}.sub{color:#555;margin-top:0}
.index{font-size:56px;font-weight:800;color:#5b21f5;margin:8px 0}
table{border-collapse:collapse;width:100%;margin:16px 0}th,td{text-align:left;padding:6px 8px;border-bottom:1px solid #eee;vertical-align:top}
.bar{background:#eee;border-radius:4px;height:10px;width:140px}.fill{height:10px;border-radius:4px;background:#5b21f5}
.band{color:#fff;border-radius:10px;padding:1px 8px;font-size:12px;white-space:nowrap}
details{border:1px solid #eee;border-radius:8px;padding:8px 12px;margin:8px 0}summary{cursor:pointer;font-weight:600}
code{background:#f3f0ff;padding:1px 4px;border-radius:3px}mark{background:#ffe08a}.muted{color:#777}
"""


def _band(band: str) -> str:
    color = BAND_COLORS.get(band, "#888")
    return f'<span class="band" style="background:{color}">{html.escape(band)}</span>'


def _bar(score) -> str:
    width = 0 if score is None else score
    return f'<div class="bar"><div class="fill" style="width:{width}%"></div></div>'



def to_html(report: NicheReport, max_rules: int = 25) -> str:
    e = html.escape
    idx = "n/a" if report.slop_index is None else str(report.slop_index)
    out: List[str] = [
        "<!doctype html><html lang=en><head><meta charset=utf-8>",
        f"<title>AI Slop Index: {e(report.niche)}</title><style>{CSS}</style></head><body>",
        f"<h1>AI Slop Index: {e(report.niche)}</h1>",
        f'<p class="sub">Live Google results via SerpApi for {", ".join("<code>" + e(q) + "</code>" for q in report.queries)}. Generated {e(report.generated_at)}.</p>',
        f'<div class="index">{idx}<span style="font-size:24px">/100</span></div>',
        f"<p>{_band(report.band)} Rank-weighted: <b>{'n/a' if report.rank_weighted_index is None else report.rank_weighted_index}</b>/100. "
        f"Scored {sum(1 for p in report.pages if p.score is not None)} of {len(report.pages)} pages. No LLM used.</p>",
        "<table><tr><th>#</th><th>Score</th><th></th><th>Band</th><th>Page</th></tr>",
    ]
    for p in report.pages:
        score = "n/a" if p.score is None else str(p.score)
        note = f'<div class="muted">skipped: {e(p.error)}</div>' if p.error else ""
        out.append(f"<tr><td>{p.rank}</td><td><b>{score}</b></td><td>{_bar(p.score)}</td><td>{_band(p.band)}</td>"
                   f'<td><a href="{e(p.url)}">{e(p.title)}</a><div class="muted">{e(p.domain)}</div>{note}</td></tr>')
    out.append("</table>")
    if report.top_rules:
        out.append("<h2>Most common patterns</h2><table><tr><th>Rule</th><th>Pages</th><th>Hits</th></tr>")
        for r in report.top_rules:
            out.append(f"<tr><td><code>{e(r['rule_id'])}</code> <span class=muted>{e(r['description'])}</span></td><td>{r['pages']}</td><td>{r['total_hits']}</td></tr>")
        out.append("</table>")
    out.append("<h2>Every matched rule, per page</h2>")
    for p in report.pages:
        if not p.hits:
            continue
        out.append(f"<details><summary>{p.rank}. {e(p.title)} ({'n/a' if p.score is None else p.score}, {e(p.band)})</summary>")
        out.append(f'<p class="muted">{p.word_count} words, {p.density_per_1k:.1f} weighted hits per 1k words</p><table>')
        for h in p.hits[:max_rules]:
            ex = "<br>".join(e(x) for x in h["examples"])
            out.append(f"<tr><td><code>{e(h['rule_id'])}</code></td><td>x{h['count']}</td><td>{ex}</td></tr>")
        if len(p.hits) > max_rules:
            out.append(f'<tr><td colspan=3 class="muted">{len(p.hits) - max_rules} more in the JSON report</td></tr>')
        out.append("</table></details>")
    out.append('<p class="muted">Scores are deterministic style-pattern scores, not a claim about who wrote a page. '
               'Made with <a href="https://github.com/Hexraei/Slopradar-SerpAPI">SlopRadar</a>.</p></body></html>')
    return "\n".join(out)

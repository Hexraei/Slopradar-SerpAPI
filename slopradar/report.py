"""Render a NicheReport for humans (terminal, Markdown) and machines (JSON)."""
from __future__ import annotations

import json
from typing import List

from .pipeline import NicheReport, PageReport


def _bar(score, width: int = 20) -> str:
    if score is None:
        return "-" * width
    filled = int(round(score / 100 * width))
    return "#" * filled + "." * (width - filled)


def _cut(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 3] + "..."


def to_json(report: NicheReport) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def to_terminal(report: NicheReport, show_rules: int = 3) -> str:
    lines: List[str] = []
    idx = "n/a" if report.slop_index is None else f"{report.slop_index}/100"
    lines.append(f"AI SLOP INDEX for \"{report.niche}\": {idx}  ({report.band})")
    if report.rank_weighted_index is not None:
        lines.append(f"Rank-weighted index (top results count more): {report.rank_weighted_index}/100")
    lines.append(f"Queries: {', '.join(report.queries)}")
    lines.append("")
    lines.append(f"{'#':>2}  {'score':>5}  {'':20}  {'band':<8}  domain / title")
    for p in report.pages:
        score = "  -  " if p.score is None else f"{p.score:>5}"
        lines.append(f"{p.rank:>2}  {score}  {_bar(p.score)}  {p.band[:8]:<8}  {p.domain}  {_cut(p.title, 60)}")
        if p.error:
            lines.append(f"{'':>34}  skipped: {p.error}")
        for h in p.hits[:show_rules]:
            example = _cut(h["examples"][0], 90) if h["examples"] else ""
            lines.append(f"{'':>34}  {h['rule_id']} x{h['count']}: \"{example}\"")
    if report.top_rules:
        lines.append("")
        lines.append("Most common patterns across the niche:")
        for r in report.top_rules[:5]:
            lines.append(f"  {r['rule_id']:<40} on {r['pages']} page(s), {r['total_hits']} hit(s)")
    lines.append("")
    lines.append(f"SerpApi calls: {report.serp_calls} (cache hits: {report.serp_cache_hits}). "
                 f"Done in {report.elapsed_seconds:.1f}s. No LLM was used to score anything.")
    return "\n".join(lines)


def _page_md(p: PageReport, max_rules: int) -> List[str]:
    out = [f"### {p.rank}. {p.title}", "",
           f"- URL: {p.url}",
           f"- Slop score: **{'n/a' if p.score is None else p.score}** ({p.band})",
           f"- Words scored: {p.word_count}, weighted hits per 1k words: {p.density_per_1k:.1f}"]
    if p.error:
        out.append(f"- Skipped: {p.error}")
    if p.hits:
        out += ["", "| Rule | Category | Hits | Example |", "|---|---|---|---|"]
        for h in p.hits[:max_rules]:
            ex = (h["examples"][0] if h["examples"] else "").replace("|", "\\|")
            out.append(f"| `{h['rule_id']}` | {h['category']} | {h['count']} | {_cut(ex, 100)} |")
        if len(p.hits) > max_rules:
            out.append(f"| ... | | | {len(p.hits) - max_rules} more rules in the JSON report |")
    out.append("")
    return out


def to_markdown(report: NicheReport, max_rules: int = 15) -> str:
    idx = "n/a" if report.slop_index is None else f"{report.slop_index}/100"
    lines = [f"# AI Slop Index: {report.niche}", "",
             f"**Index: {idx} ({report.band})**", ""]
    if report.rank_weighted_index is not None:
        lines.append(f"Rank-weighted index: {report.rank_weighted_index}/100")
    lines += [f"Queries searched via SerpApi: {', '.join('`' + q + '`' for q in report.queries)}",
              f"Generated: {report.generated_at}", "",
              "| Rank | Score | Band | Domain | Title |", "|---|---|---|---|---|"]
    for p in report.pages:
        lines.append(f"| {p.rank} | {'n/a' if p.score is None else p.score} | {p.band} | {p.domain} | {_cut(p.title, 70).replace('|', '/')} |")
    lines.append("")
    if report.top_rules:
        lines += ["## Most common patterns", "", "| Rule | Pages | Hits |", "|---|---|---|"]
        for r in report.top_rules:
            lines.append(f"| `{r['rule_id']}` | {r['pages']} | {r['total_hits']} |")
        lines.append("")
    lines += ["## Per-page detail", ""]
    for p in report.pages:
        lines += _page_md(p, max_rules)
    lines.append("_Scores are deterministic style-pattern scores, not a claim about who wrote the page._")
    return "\n".join(lines)

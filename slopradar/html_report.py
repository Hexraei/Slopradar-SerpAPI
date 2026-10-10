"""Portable, accessible report. No scripts, external fonts or tracking."""
from __future__ import annotations
import html
import base64
from pathlib import Path
from typing import List
from urllib.parse import urlparse
from .pipeline import NicheReport

CSS = """
:root{--ink:#22231f;--muted:#65685e;--line:#d4d4c9;--accent:#9a3f22;--paper:#faf9f2;--soft:#efeee4}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.5 'IBM Plex Sans',sans-serif}a{color:var(--accent);text-underline-offset:4px;overflow-wrap:anywhere}a:hover{text-decoration-thickness:2px}a:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:5px}.wrap{max-width:1240px;margin:auto;padding:32px 48px 60px}.mast{border-top:4px solid var(--ink);border-bottom:1px solid var(--ink);padding:14px 0;display:flex;justify-content:space-between;align-items:baseline;gap:20px}.brand{font:600 32px/1 'Newsreader',serif;letter-spacing:-1px}.meta{font-size:12px;letter-spacing:.5px;color:var(--muted)}.intro{margin:36px 0 28px;max-width:820px}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:1.8px;font-weight:600;color:var(--accent)}h1{font:400 76px/.98 'Newsreader',serif;letter-spacing:-2.5px;margin:16px 0 20px}h2{font:400 35px/1.05 'Newsreader',serif;letter-spacing:-.6px;margin:0}h3{font:600 18px/1.25 'IBM Plex Sans',sans-serif;margin:0}.intro p{font-size:17px;max-width:650px;color:var(--muted);margin:0}.overview{display:grid;grid-template-columns:1fr 1.5fr;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);margin:28px 0 38px}.scoreblock{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:8px 26px;padding:26px 28px 26px 0;border-right:1px solid var(--line)}.scoreblock .eyebrow{grid-column:1/-1}.number{font:400 104px/.95 'Newsreader',serif;letter-spacing:-5px;font-variant-numeric:lining-nums tabular-nums}.denom{font:400 22px 'IBM Plex Sans',sans-serif;letter-spacing:-.5px;color:var(--muted)}.verdict{font-size:15px;font-weight:600}.scale,.scale-labels{display:none}.facts{padding:28px 0 24px 32px}.facts dl{display:grid;grid-template-columns:1fr auto;gap:6px 20px;margin:0;font-size:14px}.facts dt{color:var(--muted)}.facts dd{font-weight:600;margin:0;font-variant-numeric:tabular-nums}.context{font-size:13px;color:var(--muted);margin:16px 0 0;max-width:520px}.sectionhead{display:flex;justify-content:space-between;align-items:end;gap:30px;margin:32px 0 16px}.sectionhead p{font-size:13px;color:var(--muted);margin:0;max-width:260px}.columns{display:none}.result{border-top:1px solid var(--line)}.result:last-of-type{border-bottom:1px solid var(--line)}.result summary{display:grid;grid-template-columns:24px 86px minmax(0,1fr) 110px;gap:18px;align-items:start;padding:22px 0;list-style:none;cursor:pointer}.result summary::-webkit-details-marker{display:none}.rank{font-size:11px;color:var(--muted);padding-top:6px}.metric{grid-column:2;grid-row:1;font:400 52px/1 'Newsreader',serif;font-variant-numeric:lining-nums tabular-nums;letter-spacing:-2px}.pageidentity{grid-column:3;grid-row:1}.title{font:400 26px/1.15 'Newsreader',serif;display:block;letter-spacing:-.2px}.domain{font-size:12px;color:var(--muted);margin-top:8px}.assessment{font-size:12px;text-align:right;padding-top:6px}.openhint{font-weight:600;color:var(--accent);display:block;margin-top:10px;font-size:11px;text-transform:uppercase;letter-spacing:.9px}.result[open]{background:var(--soft)}.result[open] summary{padding-left:16px;padding-right:16px}.detail{padding:0 24px 26px 146px}.detail-meta{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:var(--muted);border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:20px}.rule{border-top:1px solid var(--line);padding:18px 0}.rule:first-child{border-top:0}.rule-head{display:flex;justify-content:space-between;gap:20px}.rule-head p{font-size:12px;color:var(--muted);margin:0;white-space:nowrap}.rule code{font-size:11px;display:block;color:var(--muted);margin:8px 0;overflow-wrap:anywhere}blockquote{font:400 21px/1.35 'Newsreader',serif;margin:10px 0;padding-left:16px;border-left:2px solid var(--accent)}.reason{font-size:14px;color:var(--muted);margin:10px 0}.patterns{display:grid;grid-template-columns:1fr 1fr;gap:0 34px}.pattern{border-top:1px solid var(--line);padding:16px 0;display:flex;justify-content:space-between;gap:20px}.pattern p{font-size:14px;font-weight:500;margin:0}.pattern small{font-size:10px;color:var(--muted);overflow-wrap:anywhere}.pattern-count{font-size:12px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}.method{display:grid;grid-template-columns:1fr 2fr;gap:12px 40px;border-top:2px solid var(--ink);margin-top:38px;padding-top:24px}.method h2{grid-row:span 5}.method p,.method ul{font-size:13px;color:var(--muted);margin:0}.method ul{padding-left:18px}.foot{font-size:11px;color:var(--muted);border-top:1px solid var(--line);padding-top:16px;margin-top:28px}.empty{padding:24px 0;color:var(--muted)}
@media(max-width:650px){.wrap{padding:20px 20px 40px}.mast{padding:12px 0}.brand{font-size:28px}.meta{text-align:right;max-width:152px;font-size:10px}.intro{margin:26px 0 22px}h1{font-size:53px;letter-spacing:-1.8px;margin:13px 0 15px}.intro p{font-size:14px;line-height:1.5}.overview{grid-template-columns:1fr;margin:24px 0 28px}.scoreblock{grid-template-columns:1fr auto;border-right:0;border-bottom:1px solid var(--line);padding:20px 0;gap:10px}.scoreblock .eyebrow{grid-column:1}.number{grid-column:1;grid-row:2;font-size:82px}.verdict{grid-column:2;grid-row:2;font-size:14px}.facts{padding:18px 0}.facts dl{font-size:13px;gap:5px 16px}.context{font-size:12px;margin-top:14px}.sectionhead{display:block;margin:28px 0 16px}h2{font-size:31px}.sectionhead p{margin-top:9px;max-width:none}.result summary{grid-template-columns:18px 64px minmax(0,1fr);gap:10px;padding:19px 0}.metric{font-size:40px;letter-spacing:-1.5px}.title{font-size:22px;line-height:1.12}.rank{font-size:10px}.assessment{grid-column:3;grid-row:2;display:flex;justify-content:space-between;gap:12px;text-align:left;padding-top:0}.openhint{margin:0;font-size:10px}.domain{font-size:11px;overflow-wrap:anywhere;margin-top:7px}.result[open] summary{padding-left:10px;padding-right:10px}.detail{padding:0 14px 20px 20px}.detail-meta{gap:8px 16px;font-size:11px}.rule-head{display:block}.rule-head p{white-space:normal;margin-top:6px}h3{font-size:15px}blockquote{font-size:19px;padding-left:12px}.patterns{grid-template-columns:1fr}.pattern p{font-size:13px}.method{display:block;margin-top:30px}.method h2{margin-bottom:18px}.method p,.method ul{margin:10px 0}.foot{line-height:1.6}}
.intro{display:grid;grid-template-columns:1fr;max-width:none;margin:32px 0}.intro h1{font-size:clamp(54px,7.5vw,104px);max-width:920px;letter-spacing:-3px}.intro p{max-width:510px;margin-left:auto}.trace-section{border-top:1px solid var(--ink);padding:24px 0 28px;border-bottom:1px solid var(--ink)}.trace-top{display:flex;justify-content:space-between;gap:20px}.trace-copy{font:400 25px/1.15 'Newsreader',serif;margin:13px 0 0}.trace-index{text-align:right;min-width:130px}.trace-index .number{font-size:83px;letter-spacing:-4px;margin:10px 0 2px}.trace-index>span:last-child{font-size:12px}.fingerprint{display:block;width:100%;height:auto;max-height:300px;font-family:'IBM Plex Sans',sans-serif;margin:8px 0 0}.trace-caption{display:flex;justify-content:space-between;gap:16px;font-size:11px;color:var(--muted)}.trace-facts{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:22px;font-size:12px;color:var(--muted)}.trace-facts b{font-size:15px;color:var(--ink);font-weight:600}.trace-section .context{margin-top:12px;max-width:none}.result:target{border-top:2px solid var(--accent)}
@media(max-width:650px){.intro h1{font-size:57px;letter-spacing:-2px}.intro p{margin-left:48px;max-width:none;font-size:14px}.trace-section{padding:20px 0}.trace-top{gap:14px}.trace-copy{font-size:20px}.trace-index{min-width:112px}.trace-index .number{font-size:65px;letter-spacing:-3px}.trace-index .denom{font-size:17px}.trace-top .eyebrow{font-size:9px;letter-spacing:1.1px}.fingerprint{margin-top:18px;min-height:150px}.trace-caption{font-size:9px}.trace-facts{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px;margin-top:18px}.trace-facts b{font-size:14px}.trace-section .context{font-size:11px}.intro{margin:26px 0}}
.evidence-ribbon{display:grid;grid-template-columns:1.2fr 1fr 1.15fr;gap:24px;margin:22px 0 18px;align-items:start}.ribbon-note{color:var(--ink);text-decoration:none;border-top:2px solid var(--accent);padding-top:12px;display:block}.ribbon-note:nth-child(2){margin-top:26px}.ribbon-note:nth-child(3){margin-top:10px}.ribbon-note span{display:block;font-size:9px;letter-spacing:1px;color:var(--accent);font-weight:600;margin-bottom:8px}.ribbon-note q{font:400 20px/1.2 'Newsreader',serif}.ribbon-note:hover q{text-decoration:underline;text-underline-offset:3px}
@media(max-width:650px){.evidence-ribbon{grid-template-columns:1fr;gap:10px;margin-top:16px}.ribbon-note{padding:10px 0 0;display:grid;grid-template-columns:66px 1fr;gap:10px}.ribbon-note:nth-child(n){margin-top:0}.ribbon-note span{font-size:8px;line-height:1.5;margin:0}.ribbon-note q{font-size:17px;line-height:1.2}.ribbon-note:nth-child(n+2){display:none}.trace-copy{font-size:18px}.intro p{font-size:13px}.trace-section .context{font-size:11px}}

/* The loud atlas: ink, chartreuse, coral and deep teal. Every mark is evidence. */
:root{--ink:#18271f;--muted:#3e5146;--line:#18271f;--accent:#aa281f;--paper:#d5eb4b;--soft:#fa836d}
body{background:#d5eb4b}.wrap{max-width:1440px;padding:24px 34px 50px}.mast{border-top:0;border-bottom:3px solid var(--ink);padding:10px 0 18px}.brand{font-size:48px;letter-spacing:-2px}.meta{font:600 12px/1.3 'IBM Plex Sans';max-width:160px;border-left:3px solid var(--ink);padding-left:14px;color:var(--ink)}
.intro{display:grid;grid-template-columns:1.7fr 1fr;gap:10px 28px;margin:30px 0}.intro .eyebrow{grid-column:1/-1;background:var(--ink);color:var(--paper);padding:8px 14px;width:max-content;font-size:11px}.intro h1{font-size:clamp(74px,10vw,144px);line-height:.82;letter-spacing:-5px;margin:18px 0;grid-column:1;max-width:none}.intro p{grid-column:2;align-self:end;border-top:3px solid var(--ink);padding-top:18px;font:500 19px/1.3 'IBM Plex Sans';color:var(--ink);max-width:360px;margin:0}
.trace-section{background:#114e46;color:#ecf1ba;border:0;padding:28px 30px 24px;position:relative}.trace-top{align-items:start}.trace-top .eyebrow{color:#d5eb4b}.trace-copy{font-size:37px;max-width:570px}.trace-index{background:#fa836d;color:#18271f;transform:rotate(3deg);padding:16px 20px;min-width:200px;margin-top:-43px;border:3px solid #18271f}.trace-index .eyebrow{color:#18271f}.trace-index .number{font-size:111px;margin:6px 0}.trace-index .denom{color:#18271f}.trace-index>span:last-child{font-size:15px;font-weight:600}.fingerprint{max-height:300px;background:#f5f0d4;margin:22px 0 0;padding:12px 0;border:2px solid #18271f}.trace-facts{color:#ecf1ba;border-top:1px solid #a7c5a8;padding-top:16px}.trace-facts b{color:#d5eb4b;font-size:26px}.trace-caption{color:#ecf1ba;font-size:11px}.trace-section .context{color:#ecf1ba;font-size:12px}
.evidence-ribbon{gap:14px;margin:18px 0 20px;grid-template-columns:1.25fr 1fr 1.1fr}.ribbon-note{border:0;background:#f5f0d4;padding:18px;color:#18271f;transform:rotate(-2deg)}.ribbon-note:nth-child(2){background:#fa836d;transform:rotate(2deg);margin-top:16px}.ribbon-note:nth-child(3){background:#d5eb4b;transform:rotate(-1deg);margin-top:4px}.ribbon-note span{color:#18271f;font-size:10px}.ribbon-note q{font-size:25px}
.sectionhead{border-bottom:3px solid var(--ink);padding-bottom:16px;align-items:start;margin:32px 0 0}.sectionhead h2{font-size:59px;line-height:.9;max-width:500px}.sectionhead p{font-size:14px;color:var(--ink);max-width:220px;padding-top:8px}.result{border-top:0;border-bottom:2px solid var(--ink)}.result summary{grid-template-columns:34px 100px minmax(0,1fr) 124px;gap:20px;padding:24px 18px;background:#f5f0d4}.result:nth-of-type(even) summary{background:#fa836d}.result:nth-of-type(3n) summary{background:#b9d8ce}.result[open]{background:#f5f0d4}.result[open] summary{padding:24px 18px;border-bottom:2px solid var(--ink)}.rank{font-size:15px;font-weight:600}.metric{font-size:72px}.title{font-size:31px;letter-spacing:-.7px}.domain{color:#3e5146}.assessment{font-size:13px}.openhint{font-size:11px;color:#18271f;text-decoration:underline;text-underline-offset:4px}.detail{padding:20px 30px 26px 176px}.detail-meta{color:#3e5146;border-color:#18271f}.rule{border-color:#18271f}.rule code,.rule-head p{color:#3e5146}blockquote{border-left:4px solid #aa281f;font-size:25px}.patterns{background:#18271f;padding:0 22px;color:#f5f0d4;gap:0 38px}.pattern{border-color:#82947e;padding:20px 0}.pattern p{font:400 24px/1.15 'Newsreader';color:#f5f0d4}.pattern small,.pattern-count{color:#d5eb4b}.pattern-count{font-size:14px}.method{background:#b9d8ce;border-top:0;padding:28px;margin-top:28px}.method p,.method ul{color:#18271f;font-size:14px}.method h2{font-size:45px}.foot{color:#18271f;border-top:3px solid #18271f}
@media(max-width:650px){.wrap{padding:16px 14px 32px}.brand{font-size:34px;letter-spacing:-1px}.mast{padding:8px 0 13px}.meta{font-size:9px;max-width:117px;padding-left:8px;border-left-width:2px}.intro{display:block;margin:22px 0}.intro .eyebrow{font-size:8px;letter-spacing:1px;padding:6px 9px}.intro h1{font-size:72px;letter-spacing:-2.8px;line-height:.87;margin:20px 0}.intro p{font-size:14px;max-width:none;margin-left:54px;padding-top:10px;border-top-width:2px}.trace-section{padding:18px 14px}.trace-top{gap:14px}.trace-copy{font-size:23px;line-height:1.05;max-width:190px}.trace-index{min-width:107px;padding:10px 9px;transform:rotate(3deg);margin-top:-29px;border-width:2px}.trace-index .number{font-size:64px;letter-spacing:-3px}.trace-index .denom{font-size:14px}.trace-index .eyebrow{font-size:8px;letter-spacing:.8px}.trace-index>span:last-child{font-size:11px}.trace-top .eyebrow{font-size:8px;letter-spacing:.8px}.fingerprint{margin-top:17px;padding:8px 0;min-height:142px}.evidence-ribbon{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:14px 4px 16px}.ribbon-note{padding:12px;display:block;transform:rotate(-2deg)}.ribbon-note span{font-size:7px;line-height:1.3;margin-bottom:7px}.ribbon-note q{font-size:17px;line-height:1.12}.ribbon-note:nth-child(2){display:block;margin-top:10px;transform:rotate(2deg)}.ribbon-note:nth-child(3){display:none}.trace-caption{font-size:8px}.trace-facts{gap:8px 12px;margin-top:14px;padding-top:12px;font-size:10px}.trace-facts b{font-size:19px}.trace-section .context{font-size:10px;line-height:1.5}.sectionhead{padding-bottom:12px;margin-top:24px}.sectionhead h2{font-size:40px;max-width:none}.sectionhead p{font-size:12px;max-width:none;padding:0;margin-top:10px}.result summary{grid-template-columns:20px 76px minmax(0,1fr);gap:10px;padding:18px 11px}.result[open] summary{padding:18px 11px}.rank{font-size:11px}.metric{font-size:46px}.title{font-size:23px;letter-spacing:-.3px}.assessment{font-size:11px}.openhint{font-size:9px}.domain{font-size:10px}.detail{padding:16px 14px 22px}.detail-meta{font-size:11px}.rule-head p{font-size:11px}blockquote{font-size:21px}.patterns{padding:0 16px}.pattern p{font-size:22px}.pattern-count{font-size:11px}.method{padding:20px}.method h2{font-size:36px}.method p,.method ul{font-size:12px}.foot{font-size:10px}}
.chart-hero{margin:28px -8px 8px;border:2px solid #d5eb4b;padding:6px;background:#114e46}.fingerprint{max-height:none;margin:0;padding:0;border:0;background:#114e46}.fingerprint-mobile{display:none}.chart-legend{display:flex;flex-wrap:wrap;gap:12px 22px;border-top:1px solid #8caf98;padding:14px 14px 8px;font-size:11px;color:#ecf1ba}.chart-legend span{display:flex;align-items:center;gap:7px}.chart-legend i{width:17px;height:17px;display:inline-block;border:1px solid #18271f}.chart-legend .legend-note{margin-left:auto;color:#d5eb4b}.trace-copy{max-width:620px}.trace-caption{font-size:11px}
@media(max-width:650px){.chart-hero{margin:22px -5px 8px;padding:2px;border-width:1px}.fingerprint-desktop{display:none}.fingerprint-mobile{display:block;width:100%;min-height:0}.chart-legend{gap:9px 12px;padding:12px 9px;font-size:9px}.chart-legend i{width:12px;height:12px}.chart-legend .legend-note{margin-left:0;width:100%}.trace-copy{font-size:22px;line-height:1.05;max-width:180px}}
.meta{border:0;padding:0;background:#18271f;color:#f5f0d4;max-width:none;display:flex;align-items:center;gap:12px;font:400 18px/1.1 'Newsreader',serif;padding:12px 16px}.serp-logo{width:88px;height:auto;display:block;filter:brightness(0) invert(1)}
@media(max-width:650px){.meta{border:0;padding:8px 10px;max-width:145px;display:flex;flex-direction:column;align-items:end;gap:5px;font-size:13px}.serp-logo{width:64px}}
.chart-open{border:0;padding:0;margin:36px 0 12px}.open-chart-caption{font-size:11px;line-height:1.6;color:#b9d8ce;margin:6px 0 0 210px}.trace-copy{font-size:34px;max-width:650px}
@media(max-width:650px){.chart-open{margin:30px 0 10px}.open-chart-caption{margin-left:0;font-size:10px}.trace-copy{font-size:21px;max-width:180px}.trace-caption{font-size:9px}}
@media(max-width:650px){.meta{display:none}}
.chart-key{display:grid;grid-template-columns:1fr 1.6fr;gap:26px;border-top:2px solid #d5eb4b;margin:12px 0 22px;padding:18px 0 0}.key-title{font-size:9px;letter-spacing:1.5px;font-weight:600;color:#d5eb4b}.chart-key p{font:400 26px/1.05 'Newsreader';margin:10px 0 8px;color:#f5f0d4}.chart-key small{color:#b9d8ce;font-size:10px}.key-colors>div{display:flex;flex-wrap:wrap;gap:10px 22px;margin:12px 0}.key-colors>div span{display:flex;align-items:center;gap:8px;font-size:13px;color:#f5f0d4}.key-colors i{width:24px;height:6px;display:block}
@media(max-width:650px){.chart-key{grid-template-columns:1fr;gap:18px;padding-top:15px;margin-top:3px}.chart-key p{font-size:25px;margin-top:7px}.key-colors>div{gap:12px 22px;margin:11px 0}.key-colors>div span{font-size:12px}.chart-key small{font-size:10px}.key-colors{border-top:1px solid #56796b;padding-top:13px}}
@media print{details{break-inside:avoid}.detail{display:block}.openhint{display:none}}
"""


def _font_css() -> str:
    blocks = []
    for path in sorted((Path(__file__).parent / "assets").glob("*.woff2")):
        family = "Newsreader" if path.name.startswith("newsreader") else "IBM Plex Sans"
        weight = path.stem.rsplit("-", 1)[1]
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        blocks.append(f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(blocks)


def _safe_url(url: str) -> str:
    return url if urlparse(url).scheme in {"http", "https"} else "#"




def _plain_rule(description: str) -> str:
    return (description.replace("Inflated vocabulary:", "Word to check:")
            .replace("Hedge or filler intensifier:", "Filler or qualifier:")
            .replace("Em dash (U+2014), heavily overused in generated copy", "Em dash")
            .replace("Rhythmic 'X, Y, and Z' triplet of single words", "List of three single words")
            .replace("Tricolon of adjectives or -ly/-ive/-ful words", "List of three describing words")
            .replace("Sentence opening with a summary tag", "Opens with a summary phrase")
            .replace("Sentence opening with a stiff transition", "Opens with a formal transition")
            .replace("'From X to Y' range flourish", "'From X to Y' phrase")
            .replace("'Whether you're X or Y' audience sweep", "'Whether you're X or Y' phrase"))

def _evidence_ribbon(report: NicheReport) -> str:
    e=html.escape
    snippets=[]
    for page in report.pages:
        if page.hits:
            hit=page.hits[0]
            example=hit.get("examples", [""])[0]
            snippets.append(f'<a class=ribbon-note href="#case-{page.rank}"><span>FOUND ON PAGE {page.rank:02d}</span><q>{e(example[:170])}</q></a>')
    if not snippets:
        return '<p class=empty>No matched text to show.</p>'
    return '<div class=evidence-ribbon aria-label="Actual evidence excerpts">'+''.join(snippets[:3])+'</div>'

def _fingerprint(report: NicheReport) -> str:
    """Open horizontal score lanes: one number, one stroke, one real page."""
    e=html.escape
    colors={"structure":"#fa836d","inflated-vocabulary":"#d5eb4b","stock-phrase":"#b9d8ce","hedge":"#f5f0d4","hedge-intensifier":"#ecb960","filler":"#ecb960"}
    diagrams=[]
    for mobile in (False,True):
        width=380 if mobile else 1100
        row=55 if mobile else 65;top=46;height=top+row*max(1,len(report.pages))+35
        left=48 if mobile else 210;right=width-65;span=right-left
        variant='mobile' if mobile else 'desktop'
        out=[f'<svg class="fingerprint fingerprint-{variant}" viewBox="0 0 {width} {height}" role=img aria-labelledby="trace-title-{variant} trace-desc-{variant}"><title id="trace-title-{variant}">Page scores</title><desc id="trace-desc-{variant}">Each horizontal lane is one page in search order. Stroke length is its style-pattern score. Dashed lanes are unscored, not zero. Color names the dominant weighted rule category. Category details are in the evidence.</desc>']
        out.append(f'<text x="{left}" y="20" fill="#b9d8ce" font-size="11">0</text><text x="{left+span/2}" y="20" text-anchor="middle" fill="#b9d8ce" font-size="11">50</text><text x="{right}" y="20" text-anchor="end" fill="#b9d8ce" font-size="11">100</text>')
        for i,page in enumerate(report.pages):
            y=top+i*row
            category=max(page.category_totals,key=page.category_totals.get) if page.category_totals else ''
            color=colors.get(category,'#f5f0d4')
            out.append(f'<a href="#case-{page.rank}" aria-label="Rank {page.rank}, score {page.score if page.score is not None else "not scored"}, {e(page.title)}"><title>{e(page.domain)} / dominant category: {e(category) if category else "none"}</title>')
            out.append(f'<text x="{12 if mobile else 18}" y="{y+5}" fill="#d5eb4b" font-size="{15 if mobile else 19}" font-weight="600">{page.rank:02d}</text>')
            if not mobile:
                out.append(f'<text x="61" y="{y+5}" fill="#ecf1ba" font-size="14">{e(page.domain[:20])}</text>')
            out.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#56796b" stroke-width="1"/>')
            if page.score is None:
                out.append(f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#b9d8ce" stroke-width="2" stroke-dasharray="4 8"/><text x="{right+12}" y="{y+5}" fill="#ecf1ba" font-size="14">n/a</text>')
            else:
                x=left+span*page.score/100
                out.append(f'<line x1="{left}" y1="{y}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="{8 if mobile else 11}"/><circle cx="{x}" cy="{y}" r="{5 if mobile else 7}" fill="{color}"/><rect x="{x+7}" y="{y-20}" width="{37 if mobile else 50}" height="36" fill="#114e46"/><text x="{x+12}" y="{y+8}" fill="{color}" font-family="Newsreader" font-size="{31 if mobile else 40}">{page.score}</text>')
            out.append('</a>')
        out.append('</svg>');diagrams.append(''.join(out))
    return '<div class="chart-hero chart-open">'+''.join(diagrams)+'<div class="chart-key"><div class="key-scale"><span class="key-title">SCORE / 0-100</span><p>Line length shows the score.</p><small>Dashed lines were not scored.</small></div><div class="key-colors"><span class="key-title">MAIN RULE TYPE</span><div><span><i style="background:#fa836d"></i>Structure</span><span><i style="background:#d5eb4b"></i>Vocabulary</span><span><i style="background:#b9d8ce"></i>Stock phrases</span><span><i style="background:#ecb960"></i>Hedges</span></div><small>Open a page to see all its matches.</small></div></div></div>'

def to_html(report: NicheReport, max_rules: int = 25) -> str:
    e = html.escape
    scored = sum(p.score is not None for p in report.pages)
    idx = "n/a" if report.slop_index is None else str(report.slop_index)
    rank = "Not available" if report.rank_weighted_index is None else f"{report.rank_weighted_index}/100"
    mode = {"demo": "Offline demo / sample data", "replay": "Saved rankings / replay", "live": "Live search / SerpApi"}.get(report.source_mode, report.source_mode)
    logo = base64.b64encode((Path(__file__).parent / "assets" / "serpapi-logo.svg").read_bytes()).decode("ascii")
    provenance = f'<span class="provenance-copy">Search results from</span><img class="serp-logo" alt="SerpApi" src="data:image/svg+xml;base64,{logo}">' if report.source_mode == "live" else e(mode)
    out: List[str] = ["<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
        f"<title>SlopRadar: {e(report.niche)}</title><style>{_font_css()}{CSS}</style></head><body><main class=wrap>",
        f'<header class=mast><span class=brand>SlopRadar</span><span class=meta>{provenance}</span></header>',
        f'<section class=intro><span class=eyebrow>Page report</span><h1>{e(report.niche)}</h1><p>The pages Google returned, with scores and the text that matched.</p></section>',
        '<section class=trace-section><div class=trace-top><div><span class=eyebrow>Page scores</span><p class=trace-copy>Each line is one page, in search order. Longer lines have higher scores.</p></div>',
        f'<div class=trace-index><span class=eyebrow>Average score</span><div class=number>{idx}' + ('<span class=denom> /100</span>' if report.slop_index is not None else '') + f'</div><span>{e(report.band) if report.slop_index is not None else "No scored pages"}</span></div></div>',
        _fingerprint(report),
        _evidence_ribbon(report),
        '<div class=trace-caption><span>Search rank / first to last</span><span>Dashed = not scored</span></div>',
        f'<div class=trace-facts><span><b>{scored}/{len(report.pages)}</b> pages scored</span><span><b>{rank}</b> average, top pages count more</span><span><b>{report.serp_calls}</b> searches used</span><span><b>{report.serp_cache_hits}</b> cache hits</span></div><p class=context>This is not an AI detector. It scores the text we could read.</p></section>',
        '<div class=sectionhead><h2>Pages checked</h2><p>Open a page to see what matched.</p></div>',
        '<div class=columns aria-hidden=true><span>Rank</span><span>Page</span><span class=right>Score</span><span class=right>Assessment</span></div>']
    if not report.pages:
        out.append('<p class=empty>No pages were returned. Try a more specific query or check the saved search response.</p>')
    for p in report.pages:
        score = "n/a" if p.score is None else str(p.score)
        status = p.band if p.score is not None else "Not scored"
        out.append(f'<details class=result id="case-{p.rank}"><summary><span class=rank>{p.rank:02d}</span><span class=pageidentity><span class=title>{e(p.title)}</span><span class=domain style="display:block">{e(p.domain)}</span></span><span class=metric>{score}</span><span class=assessment>{e(status)}<span class=openhint>See matches</span></span></summary><div class=detail>')
        out.append(f'<div class=detail-meta><a href="{e(_safe_url(p.url))}" rel="noreferrer">Visit page</a><span>{p.word_count:,} words extracted</span><span>{p.density_per_1k:.1f} weighted matches per 1,000 words</span></div>')
        if p.score is None:
            out.append(f'<p class=reason>{e(p.error) if p.error else "Under 80 words of text, so it was left out of the average."}</p>')
        if p.hits:
            out.append('<div class=rules>')
            for h in p.hits[:max_rules]:
                counted = h.get('counted_hits', min(h['count'], 5))
                contribution = h.get('contribution', counted * h['weight'])
                out.append(f'<article class=rule><div class=rule-head><h3>{e(_plain_rule(h["description"]))}</h3><p>{h["count"]} found / {counted} counted / {contribution:g} weighted points</p></div><code>{e(h["rule_id"])}</code>')
                for ex in h['examples']:
                    out.append(f'<blockquote>{e(ex)}</blockquote>')
                out.append('</article>')
            if len(p.hits) > max_rules:
                out.append(f'<p class=reason>{len(p.hits) - max_rules} more matched rules are available in the JSON report.</p>')
            out.append('</div>')
        elif p.score is not None:
            out.append('<p class=reason>No rules matched this page. That does not tell us who wrote it.</p>')
        out.append('</div></details>')
    if report.top_rules:
        out.append('<div class=sectionhead><h2>Common matches</h2><p>Most pages first. Ties use the number of matches.</p></div><div class=patterns>')
        for r in report.top_rules:
            out.append(f'<div class=pattern><div><p>{e(_plain_rule(r["description"]))}</p><small>{e(r["rule_id"])}</small></div><span class=pattern-count>{r["pages"]} pages<br>{r["total_hits"]} hits</span></div>')
        out.append('</div>')
    out.append('<section class=method><h2>How scoring works</h2><p>Fixed rules check phrases and sentence shapes. Each rule counts up to five matches. Its weight and the page length determine the score. No AI model scores the text.</p><ul>')
    for warning in report.warnings:
        out.append(f'<li>{e(warning)}</li>')
    out.append('</ul><p>Search queries: ' + e(', '.join(report.queries)) + f'</p><p>Generated: {e(report.generated_at)}. Source: {e(mode)}.</p></section><footer class=foot>Made with <a href="https://github.com/Hexraei/Slopradar-SerpAPI">SlopRadar</a>. Search data from SerpApi. Open a page above to check each match in context.</footer></main></body></html>')
    return '\n'.join(out)

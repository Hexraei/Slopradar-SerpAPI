"""Compare saved reports without using another search credit.

Only common, scored URLs support a page-level score delta. A changed result
set is reported separately rather than presented as a quality improvement.
"""
from .pipeline import normalize_url


def compare_snapshots(before, after):
    if before.get("niche", "").strip().casefold() != after.get("niche", "").strip().casefold():
        raise ValueError("snapshots must describe the same niche")
    for report in (before, after):
        if not isinstance(report.get("pages"), list):
            raise ValueError("expected a SlopRadar JSON report with a pages list")
    old = {normalize_url(p["url"]): p for p in before["pages"]}
    new = {normalize_url(p["url"]): p for p in after["pages"]}
    common = []
    for key in sorted(old.keys() & new.keys()):
        a, b = old[key], new[key]
        delta = b["score"] - a["score"] if a.get("score") is not None and b.get("score") is not None else None
        common.append({"url": b["url"], "title": b.get("title", ""), "before": a.get("score"),
                       "after": b.get("score"), "delta": delta})
    old_index, new_index = before.get("slop_index"), after.get("slop_index")
    return {
        "niche": after["niche"], "before_at": before.get("generated_at", ""), "after_at": after.get("generated_at", ""),
        "before_index": old_index, "after_index": new_index,
        "index_delta": new_index - old_index if old_index is not None and new_index is not None else None,
        "common_pages": sorted(common, key=lambda p: -(abs(p["delta"]) if p["delta"] is not None else -1)),
        "added_urls": [new[k]["url"] for k in sorted(new.keys() - old.keys())],
        "removed_urls": [old[k]["url"] for k in sorted(old.keys() - new.keys())],
        "warning": "Different result sets, fetch coverage or scoring rules can change the index. Only common scored pages have a comparable delta.",
    }


def render_changes(result):
    lines = [f'SlopRadar changes: {result["niche"]}',
             f'Snapshots: {result["before_at"]} -> {result["after_at"]}',
             f'Index: {result["before_index"]} -> {result["after_index"]} (delta {result["index_delta"]})',
             result["warning"], "", "Common pages (negative delta = fewer style patterns):"]
    for page in result["common_pages"]:
        delta = "not comparable" if page["delta"] is None else f'{page["delta"]:+d}'
        lines.append(f'  {delta:>14}  {page["before"]} -> {page["after"]}  {page["url"]}')
    for label, key in [("New in results", "added_urls"), ("No longer in results", "removed_urls")]:
        lines.extend(["", f'{label}: {len(result[key])}'])
        lines.extend(f"  {url}" for url in result[key])
    return "\n".join(lines)

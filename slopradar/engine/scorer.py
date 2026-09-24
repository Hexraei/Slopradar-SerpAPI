"""Deterministic scoring. Same text in, same score out, every time."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Optional

from .rules import RULES, Rule

# A single rule can add at most this many hits, so one repeated word
# (a brand that happens to be called "Nexus Journey") cannot sink a page.
PER_RULE_CAP = 5
# Density (weighted hits per 1,000 words) that maps to a score of ~63.
DENSITY_SCALE = 25.0
MIN_WORDS = 80

BANDS = [
    (75, "Slop"),
    (50, "Sloppy"),
    (25, "Mixed"),
    (0, "Human"),
]

_WORD_RE = re.compile(r"[A-Za-z0-9\u00C0-\u024F'\u2019-]+")


@dataclass
class RuleHit:
    rule_id: str
    category: str
    description: str
    weight: float
    count: int
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SlopScore:
    score: Optional[int]
    band: str
    word_count: int
    weighted_hits: float
    density_per_1k: float
    hits: List[RuleHit]
    category_totals: Dict[str, float]

    def to_dict(self) -> Dict:
        return {
            "score": self.score,
            "band": self.band,
            "word_count": self.word_count,
            "weighted_hits": round(self.weighted_hits, 2),
            "density_per_1k": round(self.density_per_1k, 2),
            "category_totals": {k: round(v, 2) for k, v in self.category_totals.items()},
            "hits": [h.to_dict() for h in self.hits],
        }


def band_for(score: Optional[int]) -> str:
    if score is None:
        return "Too little text"
    for floor, name in BANDS:
        if score >= floor:
            return name
    return "Human"


def _context(text: str, start: int, end: int, pad: int = 40) -> str:
    left = max(0, start - pad)
    right = min(len(text), end + pad)
    snippet = text[left:right].replace("\n", " ").strip()
    return ("..." if left > 0 else "") + snippet + ("..." if right < len(text) else "")


def count_words(text: str) -> int:
    return len(_WORD_RE.findall(text))


def score_text(text: str, rules: Iterable[Rule] = RULES, max_examples: int = 3) -> SlopScore:
    """Score a block of copy. Returns every matched rule with examples."""
    words = count_words(text)
    hits: List[RuleHit] = []
    weighted = 0.0
    categories: Dict[str, float] = {}
    for rule in rules:
        matches = list(rule.pattern.finditer(text))
        if not matches:
            continue
        counted = min(len(matches), PER_RULE_CAP)
        contribution = counted * rule.weight
        weighted += contribution
        categories[rule.category] = categories.get(rule.category, 0.0) + contribution
        hits.append(RuleHit(
            rule_id=rule.id,
            category=rule.category,
            description=rule.description,
            weight=rule.weight,
            count=len(matches),
            examples=[_context(text, m.start(), m.end()) for m in matches[:max_examples]],
        ))
    hits.sort(key=lambda h: (-min(h.count, PER_RULE_CAP) * h.weight, h.rule_id))
    density = (weighted / words * 1000.0) if words else 0.0
    if words < MIN_WORDS:
        score = None
    else:
        score = int(round(100 * (1 - math.exp(-density / DENSITY_SCALE))))
    return SlopScore(
        score=score,
        band=band_for(score),
        word_count=words,
        weighted_hits=weighted,
        density_per_1k=density,
        hits=hits,
        category_totals=categories,
    )

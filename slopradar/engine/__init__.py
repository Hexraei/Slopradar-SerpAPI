"""Deterministic AI-sounding copy detection. No LLM, no network."""
from .rules import RULES, CATEGORIES, Rule
from .scorer import score_text, SlopScore, RuleHit, band_for, count_words

__all__ = ["RULES", "CATEGORIES", "Rule", "score_text", "SlopScore", "RuleHit", "band_for", "count_words"]

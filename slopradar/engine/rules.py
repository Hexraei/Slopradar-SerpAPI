"""Rule library for the SlopRadar detection engine.

Every rule is a plain, explainable pattern. There is no model and no API call
anywhere in detection. A rule has an id, a category, a weight and a regex.
Weights say how strongly a single hit suggests machine-sounding copy.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Pattern


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    description: str
    weight: float
    pattern: Pattern = field(compare=False, hash=False)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _word_regex(term: str) -> Pattern:
    # Allow simple inflections for single words (delve, delves, delving, delved).
    escaped = re.escape(term).replace(r"\ ", r"\s+")
    if " " not in term and term.isalpha():
        stem = escaped[:-1] if term.endswith("e") else escaped
        return re.compile(rf"\b{stem}(?:e|es|ed|ing|s|d)?\b", re.IGNORECASE)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _phrase_regex(phrase: str) -> Pattern:
    escaped = re.escape(phrase).replace(r"\ ", r"\s+").replace("'", "['\u2019]")
    return re.compile(rf"(?<![\w]){escaped}(?![\w])", re.IGNORECASE)


# ---------------------------------------------------------------------------
# 1. Inflated vocabulary: words that show up far more in generated copy.
# ---------------------------------------------------------------------------
INFLATED_VOCAB = [
    "delve", "tapestry", "testament", "realm", "landscape", "embark", "unleash",
    "unlock", "elevate", "empower", "leverage", "harness", "foster", "bolster",
    "streamline", "revolutionize", "transformative", "game-changer", "game-changing",
    "cutting-edge", "state-of-the-art", "groundbreaking", "unparalleled", "unprecedented",
    "unrivaled", "unmatched", "unwavering", "pivotal", "paramount", "crucial",
    "vital", "vibrant", "bustling", "meticulous", "meticulously", "intricate",
    "intricacies", "nuanced", "multifaceted", "holistic", "synergy", "synergies",
    "paradigm", "ecosystem", "journey", "beacon", "cornerstone", "linchpin",
    "bedrock", "treasure trove", "plethora", "myriad", "array", "labyrinth",
    "symphony", "kaleidoscope", "mosaic", "odyssey", "saga", "enigma",
    "captivating", "enchanting", "mesmerizing", "breathtaking", "awe-inspiring",
    "exquisite", "sublime", "resonate", "underscore", "showcase", "garner",
    "navigate", "spearhead", "orchestrate", "curate", "craft",
    "bespoke", "tailored", "optimize", "maximize", "amplify",
    "catalyze", "catalyst", "propel", "skyrocket", "supercharge", "turbocharge",
    "redefine", "reimagine", "reinvent", "demystify", "illuminate", "elucidate",
    "embrace", "enhance", "enrich", "facilitate", "utilize", "endeavor",
    "commendable", "noteworthy", "remarkable", "profound", "renowned", "esteemed",
    "illustrious", "quintessential", "indispensable", "invaluable", "insightful",
    "thought-provoking", "comprehensive", "robust", "seamless", "seamlessly",
    "effortlessly", "effortless", "intuitive", "dynamic", "innovative",
    "next-level", "world-class", "best-in-class", "top-notch", "unlocking",
    "boasts", "nestled", "tucked away", "hidden gem",
    "ever-evolving", "ever-changing", "fast-paced", "digital age", "modern era",
    "furthermore", "moreover", "additionally", "consequently", "nevertheless",
    "notably", "arguably", "undoubtedly", "undeniably", "indeed", "ultimately",
    "essentially", "fundamentally", "inherently", "intrinsically", "invariably",
    "whilst", "amidst", "henceforth", "thereby", "wherein", "therein",
    "stakeholders", "actionable", "impactful", "scalable", "frictionless",
    "mission-critical", "future-proof", "evolving landscape",
]

# ---------------------------------------------------------------------------
# 2. Hedges and filler intensifiers.
# ---------------------------------------------------------------------------
HEDGES = [
    "truly", "genuinely", "incredibly", "remarkably", "exceptionally", "immensely",
    "tremendously", "significantly", "substantially", "profoundly", "deeply",
    "highly", "utterly", "absolutely", "certainly", "definitely", "surely",
    "it is worth noting", "it's worth noting", "it is important to note",
    "it's important to note", "it is essential to", "it's essential to",
    "it is crucial to", "it's crucial to", "it is vital to", "generally speaking",
    "in many ways", "to some extent", "in essence", "at its core",
    "when it comes to", "in terms of", "a wide range of", "a wide variety of",
    "a variety of", "a myriad of", "a plethora of", "a host of", "an array of",
    "plays a crucial role", "plays a vital role", "plays a pivotal role",
    "plays a key role", "plays a significant role",
]

# ---------------------------------------------------------------------------
# 3. Stock phrases, openers and closers.
# ---------------------------------------------------------------------------
STOCK_PHRASES = [
    "in today's fast-paced world", "in today's digital age", "in today's world",
    "in today's ever-evolving", "in today's competitive", "in the modern world",
    "in an era of", "in an ever-changing world", "in the ever-evolving world of",
    "in the realm of", "look no further", "whether you're a",
    "whether you are a", "whether you're looking", "whether you are looking",
    "are you looking to", "have you ever wondered", "let's dive in", "let's dive into",
    "let's delve into", "dive deep into", "deep dive", "without further ado",
    "buckle up", "strap in", "join us as we", "join me as i", "in this article",
    "in this blog post", "in this post, we", "in this guide, we", "this guide will",
    "we'll explore", "we will explore", "let's explore", "let us explore",
    "in conclusion", "to sum up", "to summarize", "in summary", "all in all",
    "at the end of the day", "the bottom line", "final thoughts", "key takeaways",
    "the takeaway", "happy coding", "happy reading", "stay tuned",
    "the possibilities are endless", "the sky's the limit", "the sky is the limit",
    "take it to the next level", "take your business to the next level",
    "elevate your", "unlock the power of", "unlock the potential of",
    "unlock the secrets of", "unleash the power of", "harness the power of",
    "a game changer", "a testament to", "stands as a testament",
    "serves as a testament", "is a testament to", "paving the way", "pave the way",
    "shaping the future", "the future of", "a new era", "a new chapter",
    "stand out from the crowd", "stand out in a crowded", "cut through the noise",
    "one-stop shop", "one-stop solution", "your go-to", "go-to solution",
    "second to none", "like never before", "rest assured", "peace of mind",
    "at the forefront", "at the heart of", "at the intersection of",
    "a deep understanding", "a keen eye", "a passion for", "passionate about",
    "committed to excellence", "dedicated to providing", "we pride ourselves",
    "strive to", "we strive", "our mission is to", "designed to help",
    "helps you achieve", "achieve your goals", "reach new heights",
    "soar to new heights", "navigate the complexities", "navigate the world of",
    "navigating the", "ever-evolving landscape", "rapidly evolving",
    "in the digital landscape", "digital landscape", "business landscape",
    "competitive landscape", "fostering a culture", "drive growth",
    "drive innovation", "empower you to", "empowers you to", "empowering you to",
    "seamless experience", "seamless integration", "user-friendly interface",
    "tailored solutions", "tailored to your needs", "cutting-edge technology",
    "state-of-the-art technology", "innovative solutions", "robust solution",
    "comprehensive guide", "ultimate guide", "everything you need to know",
    "a must-have", "must-read", "must-try", "worth every penny",
    "i hope this helps", "feel free to", "don't hesitate to", "please don't hesitate",
    "great question", "i'd be happy to", "certainly!", "absolutely!",
    "as an ai", "as a large language model", "it's important to remember",
    "it is important to remember", "keep in mind that",
    "more than just", "isn't just", "is not just",
    "it's not just", "it is not just",
]

# ---------------------------------------------------------------------------
# 4. Structural patterns (regex). These catch sentence shapes, not words.
# ---------------------------------------------------------------------------
STRUCTURES = [
    ("em-dash", "Em dash (U+2014), heavily overused in generated copy", 1.5,
     r"\u2014"),
    ("spaced-en-dash", "Spaced en dash used as an em dash", 1.0, r"\s\u2013\s"),
    ("not-just-x-but-y", "'Not just X, but Y' construction", 3.0,
     r"\bnot\s+(?:just|only|merely|simply)\b[^.!?]{1,80}?\bbut\b"),
    ("its-not-x-its-y", "'It's not X, it's Y' reframe", 3.0,
     r"\b(?:it|this|that)(?:'s|\u2019s|\s+is)\s+not\s+(?:about\s+)?[^.!?]{1,60}?[,;.\u2014-]\s*(?:it|this|that)(?:'s|\u2019s|\s+is)\b"),
    ("isnt-x-its-y", "'X isn't Y. It's Z' reframe", 2.5,
     r"\bisn(?:'|\u2019)t\s+[^.!?]{1,60}?[.;,\u2014]\s*(?:it|this|that)(?:'s|\u2019s|\s+is)\b"),
    ("more-than-just", "'More than just X' framing", 2.0, r"\bmore\s+than\s+just\b"),
    ("tricolon-adjectives", "Tricolon of adjectives or -ly/-ive/-ful words", 1.0,
     r"\b\w+(?:ly|ive|ful|less|ous|able|ible|ent|ant)\b,\s+\w+(?:ly|ive|ful|less|ous|able|ible|ent|ant)\b,?\s+and\s+\w+(?:ly|ive|ful|less|ous|able|ible|ent|ant)\b"),
    ("tricolon-list", "Rhythmic 'X, Y, and Z' triplet of single words", 0.5,
     r"\b[A-Za-z]{4,},\s+[A-Za-z]{4,},\s+and\s+[A-Za-z]{4,}\b"),
    ("whether-or", "'Whether you're X or Y' audience sweep", 2.5,
     r"\bwhether\s+you(?:'re|\u2019re|\s+are)\s+[^.!?]{1,60}?\s+or\s+"),
    ("from-x-to-y", "'From X to Y' range flourish", 1.0,
     r"\bfrom\s+[a-z][\w-]*(?:\s+[\w-]+){0,3}\s+to\s+[a-z][\w-]*(?:\s+[\w-]+){0,3}\s*,"),
    ("rhetorical-reveal", "Rhetorical question then answer ('The result? ...')", 2.0,
     r"\b(?:the\s+(?:result|answer|catch|secret|kicker|truth|best\s+part|twist)|why|how|what)\?\s+[A-Z]"),
    ("heres-the-thing", "'Here's the thing / Here's why' setup", 2.0,
     r"\bhere(?:'s|\u2019s)\s+(?:the\s+thing|why|how|what|the\s+kicker|the\s+deal)\b"),
    ("sentence-moreover", "Sentence opening with a stiff transition", 1.5,
     r"(?:^|[.!?]\s+)(?:Moreover|Furthermore|Additionally|Consequently|Notably|Importantly|Ultimately|Indeed|Thus|Hence),"),
    ("sentence-in-short", "Sentence opening with a summary tag", 1.5,
     r"(?:^|[.!?]\s+)(?:In short|In essence|In summary|In conclusion|Overall|To conclude|Simply put|Put simply),"),
    ("colon-reveal", "Short colon reveal ('One thing: ...')", 0.8,
     r"(?:^|[.!?]\s+)(?:The\s+)?\w+(?:\s+\w+)?:\s+[A-Z][^.!?]{1,40}\."),
    ("emoji-bullet", "Emoji used as a bullet or heading marker", 1.5,
     r"(?m)^\s*[\u2705\u2728\U0001F680\U0001F4A1\U0001F525\U0001F449\U0001F4CC\U0001F31F\u2B50\U0001F3AF\U0001F4C8\U0001F512\u26A1]"),
    ("sparkle-emoji", "Rocket, sparkle or fire emoji in copy", 1.0,
     r"[\u2728\U0001F680\U0001F525\U0001F4AA\U0001F31F]"),
    ("double-adjective-noun", "'X and Y' paired adjectives before a noun", 0.5,
     r"\b(?:fast|easy|simple|powerful|secure|reliable|flexible|scalable|modern|clean|smart)\s+and\s+(?:fast|easy|simple|powerful|secure|reliable|flexible|scalable|modern|clean|smart|intuitive|efficient)\b"),
    ("ever-x-ing", "'Ever-evolving / ever-growing' compound", 1.5,
     r"\bever[- ](?:evolving|changing|growing|expanding|shifting|increasing)\b"),
    ("in-todays", "'In today's ...' opener", 2.5, r"\bin\s+today(?:'s|\u2019s)\b"),
    ("x-is-key", "'X is key' verdict", 1.0, r"\b(?:is|are)\s+(?:the\s+)?key\b[.!,]"),
    ("imagine-a-world", "'Imagine a world' / 'Picture this' hook", 2.5,
     r"\b(?:imagine\s+(?:a\s+world|if|this)|picture\s+this)\b"),
    ("say-goodbye", "'Say goodbye to X' / 'Say hello to Y'", 2.5,
     r"\bsay\s+(?:goodbye|hello)\s+to\b"),
    ("no-more", "Stacked 'No more X. No more Y.'", 2.0,
     r"\bno\s+more\s+\w+[^.!?]{0,40}[.!]\s+no\s+more\b"),
    ("its-all-about", "'It's all about X'", 1.5, r"\bit(?:'s|\u2019s)\s+all\s+about\b"),
    ("the-best-part", "'The best part?'", 2.0, r"\bthe\s+best\s+part\b"),
    ("both-and", "'Both X and Y' balance", 0.5, r"\bboth\s+\w+\s+and\s+\w+\b"),
    ("nothing-short-of", "'Nothing short of'", 2.0, r"\bnothing\s+short\s+of\b"),
    ("exclamation-cluster", "Two or more exclamation sentences in a row", 1.0,
     r"![^.!?\n]{1,80}!"),
    ("unlike-traditional", "'Unlike traditional X' contrast", 1.5,
     r"\bunlike\s+(?:traditional|conventional|other)\b"),
    ("key-feature-list", "'Key features/benefits include' list intro", 1.0,
     r"\bkey\s+(?:features|benefits|takeaways|highlights)\b"),
    ("stands-out", "'What sets X apart / stands out'", 1.5,
     r"\b(?:what\s+sets\s+\w+\s+apart|stands\s+out\s+(?:as|from))\b"),
    ("title-case-colon-heading", "'Unlocking X: The Y' headline shape", 1.5,
     r"\b(?:Unlocking|Unleashing|Mastering|Navigating|Exploring|Embracing|Harnessing)\s+[A-Z][\w\s]{2,40}:\s"),
]


def _build_rules() -> List[Rule]:
    rules: List[Rule] = []
    seen = set()

    def add(rule_id: str, category: str, description: str, weight: float, pattern: Pattern) -> None:
        if rule_id in seen:
            return
        seen.add(rule_id)
        rules.append(Rule(rule_id, category, description, weight, pattern))

    for word in INFLATED_VOCAB:
        weight = 1.0
        add(f"vocab.{_slug(word)}", "inflated-vocabulary",
            f"Inflated vocabulary: '{word}'", weight, _word_regex(word))
    for term in HEDGES:
        add(f"hedge.{_slug(term)}", "hedge-intensifier",
            f"Hedge or filler intensifier: '{term}'", 0.5 if " " not in term else 1.5,
            _word_regex(term) if " " not in term else _phrase_regex(term))
    for phrase in STOCK_PHRASES:
        add(f"phrase.{_slug(phrase)}", "stock-phrase",
            f"Stock phrase: '{phrase}'", 2.0, _phrase_regex(phrase))
    for rule_id, description, weight, regex in STRUCTURES:
        add(f"structure.{rule_id}", "structure", description, weight,
            re.compile(regex, re.IGNORECASE if not rule_id.startswith(("sentence-", "title-", "colon-", "rhetorical")) else 0))
    return rules


RULES: List[Rule] = _build_rules()

CATEGORIES = sorted({r.category for r in RULES})

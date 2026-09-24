from slopradar.engine import RULES, CATEGORIES, score_text, band_for
from slopradar.engine.scorer import MIN_WORDS, PER_RULE_CAP
from slopradar.extract import extract_text

FILLER = " The desk arrived on Tuesday and the box was heavy." * 20


def ids(result):
    return {h.rule_id for h in result.hits}


def test_library_has_300_plus_unique_rules():
    assert len(RULES) >= 300
    assert len({r.id for r in RULES}) == len(RULES)
    assert {"inflated-vocabulary", "stock-phrase", "hedge-intensifier", "structure"} <= set(CATEGORIES)


def test_every_rule_has_a_description_and_positive_weight():
    for rule in RULES:
        assert rule.description
        assert rule.weight > 0


def test_em_dash_is_flagged():
    assert "structure.em-dash" in ids(score_text("Content is king \u2014 always." + FILLER))


def test_not_just_but_construction():
    r = score_text("It is not just a desk, but a lifestyle." + FILLER)
    assert "structure.not-just-x-but-y" in ids(r)


def test_its_not_x_its_y_reframe():
    r = score_text("It's not a tool, it's a movement." + FILLER)
    assert "structure.its-not-x-its-y" in ids(r)


def test_vocab_inflections_match():
    r = score_text("We delved into it. She is delving deeper. He delves." + FILLER)
    hit = [h for h in r.hits if h.rule_id == "vocab.delve"][0]
    assert hit.count == 3


def test_word_boundaries_avoid_false_positives():
    # "arrays" is fine, "realmente" should not match "realm", "landscaper" not "landscape".
    r = score_text("The realmente landscaper parked." + FILLER)
    assert "vocab.realm" not in ids(r)
    assert "vocab.landscape" not in ids(r)


def test_slop_page_scores_high_human_page_scores_low(slop_html, human_html):
    slop = score_text(extract_text(slop_html))
    human = score_text(extract_text(human_html))
    assert slop.score >= 75 and slop.band == "Slop"
    assert human.score < 50
    assert slop.score - human.score >= 40


def test_scoring_is_deterministic(slop_html):
    text = extract_text(slop_html)
    first = score_text(text).to_dict()
    for _ in range(3):
        assert score_text(text).to_dict() == first


def test_short_text_is_not_scored():
    r = score_text("Unlock the power of seamless synergy.")
    assert r.score is None
    assert r.band == "Too little text"
    assert r.word_count < MIN_WORDS
    assert r.hits  # rules still reported


def test_per_rule_cap_limits_one_word_dominating():
    many = score_text(("Journey " * 50) + FILLER)
    hit = [h for h in many.hits if h.rule_id == "vocab.journey"][0]
    assert hit.count == 50
    assert many.weighted_hits == PER_RULE_CAP * hit.weight


def test_hits_carry_examples_with_context():
    r = score_text("Honestly, let's dive in and see." + FILLER)
    hit = [h for h in r.hits if h.rule_id == "phrase.let-s-dive-in"][0]
    assert "dive in" in hit.examples[0].lower()


def test_curly_apostrophes_match():
    r = score_text("In today\u2019s world, let\u2019s dive in." + FILLER)
    assert "phrase.let-s-dive-in" in ids(r)
    assert "structure.in-todays" in ids(r)


def test_bands():
    assert band_for(None) == "Too little text"
    assert band_for(0) == "Human"
    assert band_for(30) == "Mixed"
    assert band_for(60) == "Sloppy"
    assert band_for(90) == "Slop"

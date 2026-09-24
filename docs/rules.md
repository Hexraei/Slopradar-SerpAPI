# Writing rules

All rules live in `slopradar/engine/rules.py`. There are four kinds:

| Kind | Where | How it matches |
|---|---|---|
| Inflated vocabulary | `INFLATED_VOCAB` | Whole word, case-insensitive, simple inflections (delve, delves, delved, delving) |
| Hedges and intensifiers | `HEDGES` | Single words at weight 0.5, phrases at 1.5 |
| Stock phrases | `STOCK_PHRASES` | Exact phrase, flexible whitespace, straight or curly apostrophes |
| Structures | `STRUCTURES` | Hand-written regex with its own id, description and weight |

## Adding a rule

1. Add a word or phrase to the right list, or a tuple to `STRUCTURES`:

   ```python
   ("say-less", "'Say less' hype closer", 1.5, r"\bsay\s+less\b"),
   ```

2. Add a test in `tests/test_engine.py` with one sentence that should match and one that should not.
3. Run `pytest` and `slopradar demo` to see the effect on scores.

## Weights

- 0.25-0.5: common in human writing too, only a nudge.
- 1.0: a typical inflated word.
- 1.5-2.0: stock phrases and stiff transitions.
- 2.5-3.0: strong structural tells ("It's not X, it's Y", "Whether you're X or Y").

A rule counts at most 5 times per page. Density is weighted hits per 1,000 words, and the score is `100 * (1 - e^(-density / 25))`.

## Checking for false positives

Run a scan with `--json-out`, then look at which rules fire most across pages that read human. The rule changes in commit history marked `fix(engine)` came from exactly this: listicle headings, "Best for:" labels and plain "both X and Y" comparisons were tripping rules and got narrowed.

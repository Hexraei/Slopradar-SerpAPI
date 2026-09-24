# Five-minute walkthrough

A path through SlopRadar for reviewers. Steps 1-3 need no API key.

## 1. Install

```bash
git clone https://github.com/Hexraei/Slopradar-SerpAPI.git
cd Slopradar-SerpAPI
pip install -e ".[dev]"
pytest -q            # 47 tests, all offline
```

## 2. See the whole pipeline offline

```bash
slopradar demo --html demo.html
```

The demo feeds a sample SerpApi response and five sample pages through the same code path a live scan uses. Open `demo.html`: the listicle scores in the Slop band, the first-hand review and the forum thread land in Mixed, and the pricing page is too short to score.

## 3. Score any text

```bash
echo "In today's fast-paced world, it's not just a tool, it's a game-changer. Let's dive in." | slopradar score -
slopradar rules --category structure
```

Every point of a score traces back to a named rule with the text it matched.

## 4. Scan a live niche (1 SerpApi search)

```bash
export SERPAPI_API_KEY=...
slopradar scan "ai writing tools" --html report.html
```

Run it again and it is served from `.slopradar_cache/` at no cost.

## 5. Let Google pick the follow-up queries (3 searches)

```bash
slopradar scan "home loan" --gl in --queries 3
```

The first SerpApi response carries Google's related searches and "people also ask" questions. SlopRadar uses those as the next two queries, so the sample of the niche follows what real searchers type.

## 6. Compare markets (1 search per market)

```bash
slopradar compare "credit cards" --gl us --gl in --gl uk
```

## What to look for

- The niche index and the rank-weighted index. When they differ a lot, the top results and the long tail read differently.
- "Most common patterns": the phrases a niche leans on.
- "Not scored" rows: pages that refused automated fetches are shown, never guessed.

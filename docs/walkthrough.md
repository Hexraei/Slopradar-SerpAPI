# Five-minute walkthrough

A path through SlopRadar for reviewers. Steps 1-3 need no API key.

## 1. Install

```bash
git clone https://github.com/Hexraei/Slopradar-SerpAPI.git
cd Slopradar-SerpAPI
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q            # 82 tests, all offline
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

## 6. Web vs news (2 searches)

```bash
slopradar channels "ai writing tools"
```

## 7. Follow what is rising on Google Trends (2 searches + follow-ups)

```bash
slopradar scan "ai writing tools" --queries 3 --expand trends
```

## 8. Compare markets (1 search per market)

```bash
slopradar compare "credit cards" --gl us --gl in --gl uk
```

## What to look for

- The niche index and the rank-weighted index. When they differ a lot, the top results and the long tail read differently.
- "Most common patterns": the phrases a niche leans on.
- "Not scored" rows: pages that refused automated fetches are shown, never guessed.

## 9. Inspect evidence on a phone

Open the HTML report at a narrow window width. Source mode, coverage and score stay visible. Open a page row: each pattern lists total hits, counted hits (capped at 5) and weighted points, followed by the matched passages.

## 10. Compare snapshots

```bash
slopradar demo --json-out first.json --quiet
slopradar demo --json-out second.json --quiet
slopradar changes first.json second.json
```

No search credits used. The same fixture pages have zero score delta. A live tracking run needs fresh searches (`--no-cache`) on both dates.

## 11. Exclude a literal domain word

```bash
slopradar score travel.txt --ignore-rule vocab.journey --json
```

The exclusion is printed in the JSON. You decide whether the use is literal; the tool does not infer authorship.

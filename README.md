# SlopRadar

**An AI Slop Index for any corner of Google.**

Type a keyword or niche. SlopRadar searches Google live through [SerpApi](https://serpapi.com), fetches the pages that actually rank, and scores each one for AI-sounding copy with a deterministic rule engine. You get a ranked list of results, a slop score per page, every rule that fired with the exact text it matched, and one number for the whole niche.

No LLM is involved in scoring. Same page in, same score out, every time, and every point of the score traces back to a rule you can read.

```
$ slopradar scan "ai writing tools"
AI SLOP INDEX for "ai writing tools": 51/100  (Sloppy)
Rank-weighted index (top results count more): 36/100
```

## Why

Search results are filling up with copy that reads machine-made: "In today's fast-paced digital landscape", "It's not just a tool, it's a game-changer", "Unlock the power of seamless...". People who work in a niche feel this, but nobody can point at a number.

SlopRadar gives them one:

- **SEO and content teams** can see how flooded their niche is, and which competitors rank with templated copy.
- **Writers and marketers** can check their own pages against what ranks.
- **Developers** can lint landing pages before they ship.

"AI detectors" that are themselves AI models are opaque and unreliable. SlopRadar makes no claim about who wrote a page. It measures style patterns and shows its work.

## How it works

```
 niche / keyword
       |
       v
 +--------------+   query plan: the niche, then follow-ups from
 | 1. Planner   |   Google related searches / people-also-ask, or
 +--------------+   Google Trends rising queries (SerpApi)
       |
       v
 +--------------+   SerpApi Google Search API (engine=google)
 | 2. Search    |   Google Search (or Google News for `channels`),
 |              |   organic results only, ads dropped, cached on disk
 +--------------+
       |
       v
 +--------------+   dedupe URLs, keep top N by rank across queries,
 | 3. Fetch     |   robots.txt check, 12s timeout, 2 MB cap, HTML only
 +--------------+
       |
       v
 +--------------+   strip nav/header/footer/scripts/cookie banners,
 | 4. Extract   |   prefer <main>/<article>
 +--------------+
       |
       v
 +--------------+   390 regex rules in 4 categories, weighted,
 | 5. Score     |   capped per rule, normalised per 1,000 words
 +--------------+
       |
       v
 +--------------+   AI Slop Index (mean + rank-weighted), per-page
 | 6. Report    |   bands, top patterns, terminal / Markdown / JSON
 +--------------+
```

### SerpApi APIs used

| SerpApi API | Engine | What SlopRadar uses it for |
|---|---|---|
| Google Search | `google` | The organic results that get fetched and scored. Also Google's related searches and "people also ask" from the same response, which become follow-up queries at no extra cost (`--expand related`, the default). |
| Google Trends | `google_trends`, `data_type=RELATED_QUERIES` | Rising and top related queries for the niche, so follow-ups track what people are starting to search for (`--expand trends`). Off-topic breakouts are filtered out. |
| Google News | `google_news` | News coverage of the same niche, scored with the same rules, to compare journalism with the organic web (`slopradar channels`). |

Each gives the tool a different view of the same niche: what ranks, what is rising, and what is being reported. The sample of a niche follows what real searchers type, not what the tool guesses.

SerpApi is the data source for the whole product. Without live search results there is nothing to score: the point is to measure what Google actually shows for a query today, in a given country and language.

### Code layout

| Path | What it does |
|---|---|
| `slopradar/serp.py` | SerpApi client: builds the Google Search request, parses `organic_results`, handles errors, caches responses (never the key) |
| `slopradar/fetch.py` | Polite concurrent page fetcher with robots.txt, timeouts and size limits |
| `slopradar/extract.py` | Standard-library HTML to reader-visible text |
| `slopradar/engine/rules.py` | The rule library |
| `slopradar/engine/scorer.py` | Deterministic scoring and bands |
| `slopradar/pipeline.py` | The agent loop: plan, search, dedupe, fetch, score, aggregate |
| `slopradar/report.py` | Terminal, Markdown and JSON output |
| `slopradar/html_report.py` | Self-contained HTML report |
| `slopradar/cli.py` | `scan`, `channels`, `compare`, `demo`, `score`, `rules` commands |

The only runtime dependency is `requests`.

## Setup

Short on time? [docs/walkthrough.md](docs/walkthrough.md) is a five-minute path through every feature.

Requires Python 3.9+.

```bash
git clone https://github.com/Hexraei/Slopradar-SerpAPI.git
cd Slopradar-SerpAPI
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Get a SerpApi key from https://serpapi.com/manage-api-key and export it:

```bash
export SERPAPI_API_KEY="your_key_here"        # Windows PowerShell: $env:SERPAPI_API_KEY="your_key_here"
```

The key is read from the environment only. It is not printed, logged, or written to the cache.

## Usage

### Try it with no key

```bash
slopradar demo
```

Runs the full pipeline on a bundled sample search response and sample pages. No network, no key.

### Scan a niche live

```bash
slopradar scan "project management software"
slopradar scan "home loan interest rates" --gl in --location "Chennai, Tamil Nadu, India"
slopradar scan "standing desks" --queries 3 --num 15 --html report.html --json-out report.json
```

| Flag | Default | Meaning |
|---|---|---|
| `--queries N` | 1 | Queries to search (1-6). Each extra query is one SerpApi search. |
| `--expand` | `related` | Where extra queries come from: `related` (Google's related searches and "people also ask" from the first response, no extra call), `trends` (Google Trends rising queries, one extra call), or fixed `templates` |
| `--num N` | 10 | Pages to fetch and score |
| `--gl`, `--hl` | `us`, `en` | Google country and language |
| `--location` | none | SerpApi location string |
| `--cache-dir` | `.slopradar_cache` | Repeat runs of the same search cost nothing |
| `--no-cache` | off | Always hit SerpApi |
| `--serp-json FILE` | none | Replay a saved SerpApi response instead of searching |
| `--json` / `--json-out` / `--markdown` / `--html` | | Machine-readable and shareable reports. The HTML report is one self-contained file. |
| `--show-rules N` | 3 | Matched rules shown per page in the terminal |
| `--ignore-robots` | off | Skip robots.txt checks |

### Web vs news

```bash
slopradar channels "ai writing tools"
```

Scores the organic web results and the Google News results for the same niche and reports the gap. Two SerpApi searches. A live run from September 24, 2026:

```
AI Slop Index for "ai writing tools": organic web vs Google News (gl=us)
  web    51/100  Sloppy   5/9 pages scored
  news   32/100  Mixed    8/10 pages scored
Gap: 19 points, web pages read sloppier.
```

Full output: [examples/channels-ai-writing-tools.txt](examples/channels-ai-writing-tools.txt).

### Follow Google Trends

```bash
slopradar scan "ai writing tools" --queries 3 --expand trends
```

Adds one Google Trends call. For `ai writing tools` it picked `ai content writing tools` (+40% rising) and `chatgpt ai writing tools`, and dropped 7 suggestions that were off-topic (Trends listed "concerts" and "soup" as rising) or just rewordings of the niche. Output: [examples/trends-ai-writing-tools.txt](examples/trends-ai-writing-tools.txt).

### Compare Google markets

```bash
slopradar compare "credit cards"                       # US vs India
slopradar compare "credit cards" --gl us --gl uk --gl in
```

Runs the same niche through SerpApi once per country (`gl`) and ranks the markets by their Slop Index, with the top pattern in each and the domains that rank everywhere. One SerpApi search per market.

### Score a single page or file

```bash
slopradar score https://example.com/blog/post
slopradar score landing.html
cat copy.txt | slopradar score -
slopradar score draft.md --json
```

### Browse the rules

```bash
slopradar rules                       # counts per category
slopradar rules --category structure  # every structural rule
slopradar rules --json                # full library with regexes
```

## Example output

### Live run

A real run on September 24, 2026 against the live Google results for `ai writing tools` (US, English), 1 SerpApi search:

```
AI SLOP INDEX for "ai writing tools": 51/100  (Sloppy)
Rank-weighted index (top results count more): 36/100

 #  score                        band      domain
 1     16  ###.................  Human     emailvendorselection.com
 2    -    --------------------  Not scor  ilampadmanabhan.medium.com   skipped: HTTP 403
 3    -    --------------------  Not scor  quillbot.com                 skipped: HTTP 403
 4     70  ##############......  Sloppy    deepai.org
 5     82  ################....  Slop      ahrefs.com
 6    -    --------------------  Not scor  scribbr.com                  skipped: HTTP 403
 7     52  ##########..........  Sloppy    grammarly.com
 8     37  #######.............  Mixed     aimadesimple0.substack.com
 9    -    --------------------  Not scor  reddit.com                   skipped: blocked by robots.txt
```

Some of what fired on the #5 page:

```
phrase.elevate-your     x6   "Grammar Checker Elevate your writing with our free AI grammar checker..."
vocab.effortlessly      x16  "our AI writing tools will craft the marketing copy effortlessly."
vocab.unlock            x4   "Emoji Translator Unlock emotions with our AI translator!"
```

Live pages change, so a rerun can move the numbers a few points. The full reports from this run are in [`examples/`](examples/) as HTML, Markdown and JSON.

Pages that block automated requests are listed as "Not scored" and left out of the index rather than guessed at.

### Offline demo (`slopradar demo`)

```
AI SLOP INDEX for "ai writing tools": 64/100  (Sloppy)
Rank-weighted index (top results count more): 75/100
Queries: ai writing tools

 #  score                        band      domain / title
 1    100  ####################  Slop      demo.slopradar.test  10 Best AI Writing Tools to Supercharge Your Content in 2026
                                    structure.em-dash x2: "...aced digital landscape, content is king — and staying ahead of the curve has neve..."
                                    structure.sentence-moreover x2: "...rue one-stop shop for teams of all sizes. Moreover, its tailored solutions help you ..."
 2     38  ########............  Mixed     demo.slopradar.test  I tested 6 AI writing tools for a month. Here's what stuck.
                                    structure.heres-the-thing x1: "...tested 6 AI writing tools for a month. Here's what stuck. I write release notes and ..."
                                    vocab.journey x1: "...described our password reset page as "a journey of rediscovery.""
 3     95  ###################.  Slop      demo.slopradar.test  AI Writing Tools: The Ultimate Guide
                                    phrase.comprehensive-guide x1: "...e answer lies in AI writing tools. This comprehensive guide covers everything you ne..."
                                    phrase.everything-you-need-to-know x1: "...tools. This comprehensive guide covers everything you need to know about choosing th..."
 4     25  #####...............  Mixed     demo.slopradar.test  Ask HN-style thread: do you use AI to write docs?
                                    vocab.seamless x1: "...er it described a breaking change as a "seamless upgrade". That one made it into pro..."
                                    hedge.genuinely x1: "...docs to German and Japanese it has been genuinely good, better than the agency we pa..."
 5    -    --------------------  Too litt  demo.slopradar.test  Pricing - WriteFlow AI

Most common patterns across the niche:
  structure.sentence-moreover              on 2 page(s), 3 hit(s)
  structure.heres-the-thing                on 2 page(s), 2 hit(s)
  vocab.comprehensive                      on 2 page(s), 2 hit(s)
  vocab.journey                            on 2 page(s), 2 hit(s)
  vocab.seamless                           on 2 page(s), 2 hit(s)

SerpApi calls: 0 (cache hits: 0). Done in 0.1s. No LLM was used to score anything.
```

The JSON report (`--json`) contains everything above plus, for each page, every matched rule with its id, category, weight, hit count and up to three examples in context.

## Scoring

1. Each rule is a regex with a weight (0.5 to 3.0). Structural tells like "It's not X, it's Y" weigh more than a single inflated word.
2. A rule counts at most 5 times per page, so one repeated brand word cannot sink a page.
3. Weighted hits are divided by word count and scaled to hits per 1,000 words (density).
4. `score = 100 * (1 - e^(-density / 25))`, rounded. Pages under 80 words are reported but not scored.
5. Bands: 0-24 Human, 25-49 Mixed, 50-74 Sloppy, 75-100 Slop.
6. The niche index is the mean of scored pages. The rank-weighted index weights position 1 at 1, position 2 at 1/2, and so on, because searchers mostly read the top results.

### Rule categories

| Category | Count | Examples |
|---|---|---|
| inflated-vocabulary | 164 | delve, tapestry, testament, seamless, robust, elevate, leverage |
| stock-phrase | 149 | "in today's fast-paced world", "let's dive in", "unlock the power of", "in conclusion" |
| hedge-intensifier | 45 | "it's worth noting", "plays a crucial role", "a wide range of", truly |
| structure | 32 | em dash overuse, "not just X but Y", "It's not X, it's Y", "Whether you're X or Y", "The result? ...", tricolons, emoji bullets |

A high score means the page leans on patterns that are common in generated copy. It does not prove a page was written by AI, and a human who writes in marketing clichés will score high too. That is working as intended: the tool measures the copy, not the author.

## Cost

- One scan with default settings is **one SerpApi search**. `--queries 3` is three: the related-search suggestions come free with the first response.
- Responses are cached for repeat runs, and `--serp-json` replays a saved response for free.
- Page fetching and scoring run locally. No other paid APIs, no GPU, no model downloads.

## Tests

```bash
pytest
```

56 tests cover the rule engine (determinism, inflections, word boundaries, caps, bands, regression tests for false positives seen on live pages), HTML extraction, the SerpApi client (request parameters, error handling, caching that never stores the key, related-search parsing, Google News cluster flattening, Google Trends ordering and off-topic filtering on a recorded response), the pipeline (dedupe, ranking, index math, unscored pages, SerpApi-driven query expansion), the HTML report, the market and web-vs-news comparisons and the CLI. All SerpApi and page responses in the test suite are mocked, so the suite runs offline and uses no searches.

## Limitations

- Sites behind bot protection (Cloudflare and similar) often return 403. They are reported as not scored.
- The rules target English copy.
- Short pages (under 80 words) are not scored because a couple of hits would swing the result.
- Rule weights are hand-tuned. They are all visible in `slopradar/engine/rules.py`, and [docs/rules.md](docs/rules.md) explains how to add or tune one.

## Roadmap

- Track a niche over time and chart the index week by week.
- Per-domain history, to spot sites that switched to templated content.
- Project-level allowlists for words that are legitimate in a niche.

## Disclosure

- **Prior work:** SlopRadar's detection approach comes from [Voxfold](https://github.com/Hexraei/VoxfoldWeb), my deterministic anti-slop copy linter that existed before this hackathon. The rule engine in this repository is a new Python implementation written for SlopRadar, following Voxfold's approach and rule categories. The SerpApi search, fetching, pipeline, index and reporting are all new.
- **AI tools:** Built with AI coding assistance (Claude Code). The detection engine itself uses no LLM or model of any kind: it is pure pattern matching.

## License

[MIT](LICENSE)

Built by Navin Venkatesan ([@Hexraei](https://github.com/Hexraei)) for the SerpApi India Hackathon 2026.

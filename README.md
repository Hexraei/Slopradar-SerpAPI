# SlopRadar

**An AI Slop Index for any corner of Google.**

## In plain English

A lot of what shows up on Google now reads like it was churned out by a chatbot: "In today's fast-paced digital landscape...", "Unlock the power of...", "It's not just a tool, it's a game-changer." People call this kind of filler **AI slop**.

SlopRadar tells you how much of it is in the search results for any topic.

1. You type a topic, for example `ai writing tools`.
2. SlopRadar runs that search on Google right now and gets the same results a real person would see.
3. It opens each of the top pages and reads the text.
4. It checks the text against a list of 390 known "slop" patterns: overused words, stock phrases, empty filler and tell-tale sentence shapes.
5. It gives each page a score from 0 to 100, and the whole topic one overall number: the **AI Slop Index**.

It also shows its work. For every page you see exactly which patterns it found and the sentence each one came from, so you never have to take a score on trust.

```
$ slopradar scan "ai writing tools"
AI SLOP INDEX for "ai writing tools": 51/100  (Sloppy)
Rank-weighted index (top results count more): 36/100
```

### What the numbers mean

| Score | Label | In practice |
|---|---|---|
| 0-24 | Human | Reads like a person wrote it. Few or no stock patterns. |
| 25-49 | Mixed | Some filler, but mostly normal writing. |
| 50-74 | Sloppy | Leans on stock phrases and buzzwords. |
| 75-100 | Slop | Packed with them, sentence after sentence. |

The **rank-weighted index** counts the top results more heavily, because most people only read the first few. If it is lower than the plain index (as above), the very top of Google is cleaner than the rest of page one.

### No AI judging AI

SlopRadar does not use an AI model to decide what is AI-sounding. It uses plain, readable rules, like a spell checker for clichés. That means:

- The same page always gets the same score.
- Every point of a score traces back to a rule you can read.
- It makes no claim about *who* wrote a page. A human who writes in marketing clichés will score high too. It measures the writing, not the author.

### Who it is for

- **SEO and content teams** (people whose job is getting pages to rank on Google) can see how flooded their topic is, and which competitors rank with templated copy.
- **Writers and marketers** can check their own pages against what ranks.
- **Developers** can check landing-page copy before it ships.

### Where the search results come from

SlopRadar gets its Google results from [SerpApi](https://serpapi.com), a service that runs a Google search and hands back the results in a tidy, machine-readable form. SlopRadar uses three of its tools:

- **Google Search**, for the regular results that get scored.
- **Google News**, to compare news articles with the regular web on the same topic.
- **Google Trends**, to find what people are starting to search for around a topic, so the scan follows real interest.

The rest of this README goes into setup, commands and the technical details.

## How it works

In short: pick the searches, run them on Google, download the top pages, keep only the readable article text, score it, and write up the results. The diagram below is the same thing with the technical details.

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

What the technical terms mean:

- **Organic results** are the normal Google results, not ads.
- **robots.txt** is a file where a site says which pages automated tools may visit. SlopRadar respects it and skips pages it is asked to skip.
- **Regex rules** (regular expressions) are text patterns a program can search for, such as "unlock the power of" or "It's not X, it's Y".
- **Normalised per 1,000 words** means a long page is not punished just for being long: hits are counted relative to the amount of text.

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
| `slopradar/pipeline.py` | The main loop that runs each step in order: plan the searches, search, remove duplicate pages, fetch, score, combine the results |
| `slopradar/report.py` | Terminal, Markdown and JSON output |
| `slopradar/html_report.py` | Self-contained HTML report |
| `slopradar/cli.py` | `scan`, `channels`, `compare`, `demo`, `score`, `rules` commands |

The only third-party library it needs to run is `requests`.

## Setup

Short on time? [docs/walkthrough.md](docs/walkthrough.md) is a five-minute path through every feature.

You need Python 3.9 or newer. The commands below download the code, create an isolated Python environment (`.venv`) so nothing clashes with other projects, and install SlopRadar.

```bash
git clone https://github.com/Hexraei/Slopradar-SerpAPI.git
cd Slopradar-SerpAPI
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

To run live searches you need a SerpApi API key, which is like a password that lets the tool use your SerpApi account. The free plan gives 100 searches a month. Get your key from https://serpapi.com/manage-api-key and set it in your terminal:

```bash
export SERPAPI_API_KEY="your_key_here"        # Windows PowerShell: $env:SERPAPI_API_KEY="your_key_here"
```

The key is read from the environment only. It is not printed, logged, or written to the cache.

## Usage

### Try it with no key

```bash
slopradar demo
```

Runs the whole process on a saved sample search and sample pages that ship with the code. No internet connection and no key needed, so it is the quickest way to see what the output looks like.

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
| `--gl`, `--hl` | `us`, `en` | Which country's Google (`in` for India, `uk` for the UK) and which language |
| `--location` | none | Search as if from a specific city, e.g. `"Chennai, Tamil Nadu, India"` |
| `--cache-dir` | `.slopradar_cache` | Where saved search results are kept, so repeating the same search costs nothing |
| `--no-cache` | off | Always hit SerpApi |
| `--serp-json FILE` | none | Use a saved search result file instead of searching again |
| `--json` / `--json-out` / `--markdown` / `--html` | | Save the report in other formats. JSON is for other programs, Markdown and HTML are for sharing. The HTML report is a single file you can open in any browser. |
| `--show-rules N` | 3 | Matched rules shown per page in the terminal |
| `--ignore-robots` | off | Skip robots.txt checks |

### Web vs news

```bash
slopradar channels "ai writing tools"
```

Are news articles about a topic written any better than the regular web pages about it? This command scores both and reports the difference. Two SerpApi searches. A live run from September 24, 2026:

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

Does Google show more slop in one country than another? This runs the same search in each country and ranks the countries by their Slop Index, with the top pattern in each and the domains that rank everywhere. One SerpApi search per market.

### Score a single page or file

Check any one page, file or piece of text you have, such as your own blog post before publishing. This runs locally and uses no SerpApi searches.

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

The short version: count the slop patterns on a page, adjust for how long the page is, and turn that into a 0-100 score where each extra hit matters a little less than the one before. The exact steps:

1. Each rule is a regex with a weight (0.5 to 3.0). Structural tells like "It's not X, it's Y" weigh more than a single inflated word.
2. A rule counts at most 5 times per page, so one repeated brand word cannot sink a page.
3. Weighted hits are divided by word count and scaled to hits per 1,000 words (density).
4. `score = 100 * (1 - e^(-density / 25))`, rounded. Pages under 80 words are reported but not scored.
5. Bands: 0-24 Human, 25-49 Mixed, 50-74 Sloppy, 75-100 Slop.
6. The niche index is the mean of scored pages. The rank-weighted index weights position 1 at 1, position 2 at 1/2, and so on, because searchers mostly read the top results.

**Worked example.** A 600-word page has 9 weighted hits. That is 9 / 600 x 1,000 = 15 hits per 1,000 words. The score is 100 x (1 - e^(-15/25)) = 45, which is Mixed. At 25 hits per 1,000 words the score is 63 (Sloppy), and at 50 it is 86 (Slop). The curve flattens near 100, so a page cannot go past 100 however much slop it has, and the difference between "some" and "a lot" stays visible.

### Rule categories

| Category | Count | Examples |
|---|---|---|
| inflated-vocabulary (buzzwords) | 164 | delve, tapestry, testament, seamless, robust, elevate, leverage |
| stock-phrase (clichés) | 149 | "in today's fast-paced world", "let's dive in", "unlock the power of", "in conclusion" |
| hedge-intensifier (filler that pads or oversells) | 45 | "it's worth noting", "plays a crucial role", "a wide range of", truly |
| structure (sentence shapes) | 32 | em dash overuse, "not just X but Y", "It's not X, it's Y", "Whether you're X or Y", "The result? ...", tricolons (lists of exactly three for rhythm), emoji bullets |

A high score means the page leans on patterns that are common in generated copy. It does not prove a page was written by AI, and a human who writes in marketing clichés will score high too. That is working as intended: the tool measures the copy, not the author.

## Cost

SerpApi's free plan gives 100 searches a month, so SlopRadar is careful with them.


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

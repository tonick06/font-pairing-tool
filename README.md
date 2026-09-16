# Font Pairing & Typography Analysis Tool

Analyzes font files programmatically and recommends well-matched font
pairings based on measurable typographic properties extracted directly from
the font files — no external ratings, no ML model, no manual curation.

## How it works

1. **Extraction** ([src/extract_metrics.py](src/extract_metrics.py)) reads a `.ttf`/`.otf` file with
   `fontTools` and pulls out `unitsPerEm`, x-height, cap-height, ascender/
   descender, weight class, width class, and an approximate stroke-contrast
   measurement (rendered via Pillow and measured geometrically on glyph `O`).
   Category (serif/sans/slab/display/mono) comes from a hand-curated lookup
   table ([src/category_lookup.py](src/category_lookup.py)) keyed by family name, since that
   information isn't reliably present in the font file itself.
2. **Database** ([src/build_database.py](src/build_database.py)) runs the extractor across every font in
   `fonts/` and stores the results in a SQLite database at `data/metrics.db`.
   Currently 146 fonts across all five categories (serif, sans-serif,
   slab-serif, display, monospace) — see [src/download_fonts.py](src/download_fonts.py),
   [src/download_monospace.py](src/download_monospace.py), [src/download_more_categories.py](src/download_more_categories.py),
   [src/download_popular_fonts.py](src/download_popular_fonts.py), and [src/download_retry_failures.py](src/download_retry_failures.py)
   for how they were fetched from Google Fonts.
3. **Scoring** ([src/scoring.py](src/scoring.py)) combines four normalized axes — x-height
   compatibility, category contrast, weight compatibility, and stroke-contrast
   similarity — into a transparent weighted sum. Every score is traceable back
   to specific metrics; there's no hidden model.
4. **Validation** ([src/validate.py](src/validate.py)) checks the scoring function against a
   hand-built set of known-good and known-bad pairings
   ([validation/known_pairings.json](validation/known_pairings.json)) and reports whether it separates
   them with a clear margin. This doubles as a regression test.
5. **Recommendation** ([src/recommend.py](src/recommend.py)) exposes `recommend_pairings(font_name)`
   and `score_pair(font_a, font_b)` as a small API.
6. **Rendering** ([src/render.py](src/render.py)) produces demo-able PNG samples: a heading set in
   font A, a body paragraph set in font B, and the compatibility score/
   explanation underneath.

## Setup

```bash
pip install -r requirements.txt
python src/download_fonts.py       # pulls font families from Google Fonts into fonts/
python src/download_monospace.py   # fills in the monospace category (see EVOLUTION_LOG.md cycle 1)
python src/build_database.py       # extracts metrics into data/metrics.db
python src/validate.py             # sanity-checks the scoring function
```

## Usage

The `fontpair` CLI is the easiest way to use the tool day-to-day:

```bash
python fontpair.py recommend "Playfair Display" --top 5
python fontpair.py score "Playfair Display" "Source Sans 3"
python fontpair.py render "Playfair Display" "Source Sans 3" --out output/
python fontpair.py list --category serif
python fontpair.py compare path/to/fontA.ttf path/to/fontB.ttf --render
```

`compare` works on any two font files, not just ones in the database — no need to download or catalog a
font first to see how it pairs with something else.

Or call the underlying modules directly:

```bash
python src/recommend.py "Playfair Display"                      # rank the database against a font
python src/recommend.py "Playfair Display" "Source Sans 3"      # score a specific pair, with a breakdown
python src/render.py "Playfair Display" "Source Sans 3"         # render a demo image for a pairing
```

## Web app

```bash
python app.py    # then open http://localhost:5000
```

A full multi-page site, not just a single form:

| Page | What it does |
|---|---|
| `/` | Landing page with live database stats (font count per category) and links into the rest of the site |
| `/recommend` | Pick a font from the database, see its top 5 pairings rendered inline |
| `/compare` | Two ways to bring your own fonts: compare two files directly, or upload one and rank it against every font already in the database. Fonts you upload are persisted into the database, so they show up in Recommend/Browse afterward too |
| `/browse` | Every font in the database with its measured metrics, filterable by category, linking straight into Recommend |
| `/about` | The scoring methodology, weights table, and live validation numbers (pairing count, margin) — computed on page load, never hardcoded, so it can't go stale |

Templates live in `templates/`, shared styling in `static/style.css`.

## Scoring axes

| Axis | Weight | What it measures |
|---|---|---|
| category contrast | 0.50 | Serif+sans (etc.) reads as intentional hierarchy; same-category pairings score lower |
| x-height compatibility | 0.20 | Closer x-height ratios pair better for mixed body text at similar sizes |
| weight compatibility | 0.20 | Peaks at a moderate weight gap — enough for hierarchy, not so much it looks accidental |
| stroke-contrast similarity | 0.10 | Two faces with similar stroke-contrast character tend to look coherent together |

Weights started equal (0.25 each), which gave no clean separation on the
validation set (margin 0.033). A grid search (see EVOLUTION_LOG.md and
`validate.py`) found category contrast is by far the strongest signal, so
it was weighted up. Current result: clean separation across 36 known-good/
known-bad pairings spanning all five categories, margin 0.205.

Note: `weight_compat` currently can't differentiate anything, since every
downloaded font is Regular/400 — the database has no bold-weight data yet
(a known gap, see PROGRESS.md).

## Repo structure

See the tool spec this was built from for the intended layout; it's followed
as-is:

```
fonts/          downloaded .ttf/.otf files (not committed; re-run download_fonts.py)
data/           SQLite metrics database
src/            extraction, scoring, recommendation, and rendering code
validation/     known-good / known-bad pairing reference set
output/         rendered pairing sample images
tests/          pytest suite covering extraction and scoring
fontpair.py     CLI (recommend / score / render / list / compare)
app.py          Flask web app (see "Web app" section above)
templates/      Jinja templates for the web app (base layout + one per page)
static/         shared CSS for the web app
PROGRESS.md     current status and next steps (for picking work back up)
EVOLUTION_LOG.md  log of the post-v1 self-improvement loop
```

## Post-v1: self-evolution loop

Once the six milestones above were complete, the project went into an ongoing
self-directed improvement loop (assess a gap, propose it in `EVOLUTION_LOG.md`,
implement, re-validate, commit) that has run for 12+ cycles so far. See that
file for the full, dated record — highlights: filled the monospace and
slab-serif/display category gaps, bulk-added popular fonts (database grew
79 -> 136 fonts across cycles 7 and 9), added the `fontpair` CLI and a
score-any-two-files feature (no database entry required), built a
self-contained HTML gallery, fixed a real font-metadata extraction bug found
via a data-integrity audit, and grew the validation set from 16 to 44
pairings across all five categories. This file's numbers (font count,
pairing count) reflect whatever the most recent cycle left off at — check
`EVOLUTION_LOG.md` and `PROGRESS.md` for the current state, since the loop
may have continued after this paragraph was last updated.

## Non-goals (v1)

- No machine learning — scoring is a transparent, hand-designed function
- No variable-font axis space — every font is treated as fixed-weight
  (variable fonts are instanced to `wght=400` at download time)
- No accounts, auth, or persistence beyond the local SQLite file

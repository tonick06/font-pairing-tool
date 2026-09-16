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
python src/download_fonts.py     # pulls ~70 fonts from Google Fonts into fonts/
python src/build_database.py     # extracts metrics into data/metrics.db
python src/validate.py           # sanity-checks the scoring function
```

## Usage

```bash
# Rank the database against a font
python src/recommend.py "Playfair Display"

# Score a specific pair, with a breakdown
python src/recommend.py "Playfair Display" "Source Sans 3"

# Render a demo image for a pairing
python src/render.py "Playfair Display" "Source Sans 3"
```

## Scoring axes

| Axis | Weight | What it measures |
|---|---|---|
| x-height compatibility | 0.30 | Closer x-height ratios pair better for mixed body text at similar sizes |
| category contrast | 0.30 | Serif+sans (etc.) reads as intentional hierarchy; same-category pairings score lower |
| weight compatibility | 0.20 | Peaks at a moderate weight gap — enough for hierarchy, not so much it looks accidental |
| stroke-contrast similarity | 0.20 | Two faces with similar stroke-contrast character tend to look coherent together |

Weights were started equal and adjusted based on which separated the
known-good/known-bad validation set most cleanly (see `validate.py` output).

## Repo structure

See the tool spec this was built from for the intended layout; it's followed
as-is:

```
fonts/          downloaded .ttf/.otf files (not committed; re-run download_fonts.py)
data/           SQLite metrics database
src/            extraction, scoring, recommendation, and rendering code
validation/     known-good / known-bad pairing reference set
output/         rendered pairing sample images
```

## Non-goals (v1)

- No machine learning — scoring is a transparent, hand-designed function
- No variable-font axis space — every font is treated as fixed-weight
  (variable fonts are instanced to `wght=400` at download time)
- No accounts, auth, or persistence beyond the local SQLite file

# Progress

## Done
- Milestone 1 (font parsing pipeline): [src/extract_metrics.py](src/extract_metrics.py) + [src/category_lookup.py](src/category_lookup.py).
  Validated on Georgia (serif, high stroke contrast 0.36) vs Arial (sans-serif, low contrast 0.82) — matches known reality.
- Milestone 2 (font database): [src/download_fonts.py](src/download_fonts.py) pulled 58 families from Google Fonts
  (GitHub's unauthenticated API rate limit — 60 req/hr — cut the run short of the full ~76-family list, so it
  was stopped once past the spec's 50-font minimum; monospace fonts didn't make it in before the cutoff).
  [src/build_database.py](src/build_database.py) extracted all 58 with 0 failures and 0 unknown categories into
  `data/metrics.db`. Spot-check: serifs cluster low on stroke_contrast (Playfair Display 0.175, Cormorant 0.30),
  sans-serifs cluster high (0.78-1.0), slab-serifs correctly read as low-contrast (0.8-0.94) — matches real
  typographic characteristics.
- Test suite added under `tests/` (pytest) covering extraction and scoring; 8/8 passing.
- Milestone 3 (scoring.py, validate.py, known_pairings.json) — written, not yet validated against the real DB.
- Milestone 4 (recommend.py), Milestone 5 (render.py), Milestone 6 (app.py) — written, not yet run end-to-end.

## In progress
- Running Milestone 3 validation against the built database next.

## Next step
- Run `python src/validate.py`, tune weights if separation isn't clean, commit Milestone 3.
- Run recommend.py and render.py against real data, commit Milestones 4-5.
- Install Flask deps, smoke-test app.py, commit Milestone 6.
- After all 6 milestones are committed, start the self-evolution loop per the user's instructions
  (assess -> propose in EVOLUTION_LOG.md -> implement -> validate -> commit -> update this file),
  for up to 5 cycles, without changing the core weighted-sum scoring philosophy without asking first.
  Known gap for the loop to pick up: no monospace fonts in the database yet — download_fonts.py needs
  either a GITHUB_TOKEN (to raise the rate limit) or a resumable re-run to fill that category in.

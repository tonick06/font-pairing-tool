# Progress

## Done
- Milestone 1 (font parsing pipeline): [src/extract_metrics.py](src/extract_metrics.py) + [src/category_lookup.py](src/category_lookup.py).
  Validated on Georgia (serif, high stroke contrast 0.36) vs Arial (sans-serif, low contrast 0.82) - matches known reality.
- Milestone 2 (font database): 58 fonts downloaded and extracted with 0 failures, 0 unknown categories, into
  `data/metrics.db`. GitHub's unauthenticated API rate limit (60 req/hr) cut the download short of the full
  ~76-family list; monospace fonts didn't make it in. Noted as a follow-up.
- Test suite under `tests/` (pytest), 8/8 passing.
- Milestone 3 (scoring function + validation): [src/scoring.py](src/scoring.py) combines x-height compatibility,
  category contrast, weight compatibility, and stroke-contrast similarity into a weighted sum.
  Equal starting weights (0.25 each) gave no clean separation on the validation set (margin 0.033).
  A grid search found category_contrast is by far the strongest signal here, so weights were retuned to
  `{category_contrast: 0.50, x_height_compat: 0.20, weight_compat: 0.20, stroke_contrast_similarity: 0.10}`.
  This gives clean separation: every known-good pairing (avg 0.618) outscores every known-bad pairing (avg 0.406),
  margin 0.213. See [validation/known_pairings.json](validation/known_pairings.json) and `python src/validate.py`.
  Note: weight_compat is currently uninformative (every downloaded font is Regular/400, so every pair scores 0
  on that axis identically) - it doesn't hurt the margin since it's constant, but it isn't pulling its weight
  either. Fixed once bold weights are added to the database.

## In progress
- Milestones 4-6 (recommend.py, render.py, app.py) are written but not yet run end-to-end against the real DB.

## Next step
- Run recommend.py and render.py against real data, commit Milestones 4-5.
- Smoke-test app.py, commit Milestone 6.
- Then start the 5-cycle self-evolution loop (assess -> propose in EVOLUTION_LOG.md -> implement -> validate ->
  commit -> update this file). Do not change the core weighted-sum scoring philosophy without asking first.
  Known gaps for the loop: no monospace fonts in the DB; weight_compat axis needs bold-weight data to be useful;
  validation set is small (15 pairings) and could be expanded for a more robust weight search.

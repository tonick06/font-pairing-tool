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

- Milestone 4 (recommendation API): `recommend_pairings` / `score_pairing` in [src/recommend.py](src/recommend.py).
  Spot-checked Playfair Display -> top 5 are all sans-serifs with closely matched x-height; plausible to a human eye.
- Milestone 5 (visual output): [src/render.py](src/render.py) renders heading+body PNG samples with score/explanation.
  Generated a demo batch in `output/` for Playfair Display, Oswald, and Merriweather's top 3 pairings.
- Milestone 6 (web UI, stretch): [app.py](app.py) is a minimal Flask app - dropdown of every font in the DB,
  shows top-5 pairing images inline. Smoke-tested in a real browser (localhost:5000): dropdown populates,
  selecting "Playfair Display" renders 5 pairing cards, all 5 pairing images return 200 OK over the network.
  All 6 base milestones are now complete and committed.

## Evolution loop
- Cycle 1 (see EVOLUTION_LOG.md): filled the monospace category gap. Downloaded 11/12 target monospace
  families (PT Mono's expected filenames all 404'd) directly from raw.githubusercontent.com, bypassing the
  api.github.com rate limit that stalled the original download. DB now has 69 fonts across all 5 categories
  (serif, sans-serif, slab-serif, display, monospace). No regression: validation margin unchanged (0.213,
  clean separation), 8/8 tests still pass. Spot-checked JetBrains Mono -> plausible sans-serif pairings.

- Cycle 2 (see EVOLUTION_LOG.md): checked whether weight_class/width_class could be made useful (both are
  constant across the DB, all fonts Regular/Normal — a real fix needs a second weight per family plus
  disambiguating rows sharing a family_name, which is a bigger schema change than fits one cycle; flagged
  below for a future cycle instead). Added `fontpair.py`, a CLI wrapping recommend/score/render/list so the
  tool is usable without editing scripts by hand. Smoke-tested all four subcommands.

- Cycle 3 (see EVOLUTION_LOG.md): improved the renderer. Added a second, smaller heading size below the hero
  headline so a rendered sample shows how the pairing holds up at more than one scale. Fixed the meta caption
  (font names + score explanation) to wrap instead of running off the canvas edge, and font loading now raises
  a clear "could not render X (path)" error instead of a bare traceback. Regenerated the demo batch in
  `output/` (Playfair Display, Oswald, JetBrains Mono x top 3) - all clean, all captions fully visible.

## Next step
- Continue the self-evolution loop (cycle 4 of 5) (assess -> propose in EVOLUTION_LOG.md -> implement -> validate ->
  commit -> update this file). Do not change the core weighted-sum scoring philosophy without asking first.
  Known gaps for the loop to consider: no monospace fonts in the DB (download_fonts.py needs a GITHUB_TOKEN to
  get past the 60 req/hr unauthenticated rate limit, or a resumable re-run); weight_compat axis is currently
  uninformative since every downloaded font is Regular/400 (no bold weights in the DB yet); validation set is
  small (15 pairings, 13 matched fonts) and could be expanded for a more robust weight search; category_contrast
  matrix and category_lookup.py table are hand-curated and could use a second pass for edge cases.

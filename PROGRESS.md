# Progress

## Done
- Milestone 1 (font parsing pipeline): [src/extract_metrics.py](src/extract_metrics.py) + [src/category_lookup.py](src/category_lookup.py).
  Validated on Georgia (serif, high stroke contrast 0.36) vs Arial (sans-serif, low contrast 0.82) — matches known reality.

## In progress
- Milestone 2 (font database): [src/download_fonts.py](src/download_fonts.py) is running in the background,
  pulling ~70 families from Google Fonts (instancing variable fonts to a static wght=400 where needed).
  [src/build_database.py](src/build_database.py) is written but not yet run against the full set.

## Next step
- Once the download finishes, run `python src/build_database.py`, then commit Milestone 2.
- Milestone 3 (scoring.py, validate.py, known_pairings.json), Milestone 4 (recommend.py),
  Milestone 5 (render.py), and Milestone 6 (app.py) are already written in the working tree
  but not yet validated end-to-end against the real database or committed.
- After all 6 milestones are committed, start the self-evolution loop per the user's instructions
  (assess -> propose in EVOLUTION_LOG.md -> implement -> validate -> commit -> update this file),
  for up to 5 cycles, without changing the core weighted-sum scoring philosophy without asking first.

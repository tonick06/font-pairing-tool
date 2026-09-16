# Evolution Log

Record of the self-directed improvement loop that runs once Milestones 1-6
are complete and committed. Each entry states what's about to change and why,
before the change is made, so the loop stays auditable.

Guardrail: the core scoring philosophy (a simple, interpretable, weighted
sum of hand-designed axes) must not be replaced with something fundamentally
different (e.g. a trained/learned model) without flagging it to the user
first and getting explicit go-ahead.

---

## Cycle 1: Fill the monospace category gap

The database has zero monospace fonts (the initial download was cut short by
GitHub's unauthenticated API rate limit before reaching that part of the
family list), so `category_contrast` — the scoring function's strongest
axis — has never actually been validated against a monospace pairing.
Fixing this by downloading monospace families directly from
raw.githubusercontent.com (which isn't subject to the api.github.com
60 req/hr listing limit that stalled the first run), probing a short list
of known static/variable filename patterns per family instead of listing
each folder.

---

## Cycle 2: Add a proper CLI

Checked whether weight_class/width_class could be made useful next (they're
currently constant across the whole DB — every downloaded font is Regular/
Normal — so weight_compat never actually differentiates anything). Fixing
that means downloading a second weight per family and disambiguating rows
that share a family_name throughout recommend.py/render.py/app.py — a real
schema change with meaningful blast radius, not a single-commit-sized fix.
Deferring it (flagged in PROGRESS.md for a future cycle) in favor of a
contained, self-contained improvement this cycle: a `fontpair` CLI so the
tool is usable without editing scripts by hand, per the user's suggested
candidate list.

---

## Cycle 3: Improve the visual renderer

The Milestone 5 renderer only ever shows the heading at one size (48px),
which doesn't demonstrate how a pairing holds up across the sizes it'd
actually be used at (a large hero headline vs. a smaller section heading).
It also has no explicit handling if a font file fails to load or render at
all — it would just crash with a raw Pillow/fontTools traceback. Adding a
second, smaller heading size to the rendered sample, and a clear error
message (naming the font and file) instead of a bare traceback when a font
can't be rendered.

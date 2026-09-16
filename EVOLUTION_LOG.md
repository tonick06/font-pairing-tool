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

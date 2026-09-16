"""Milestone 3: the font-pairing compatibility scoring function.

Design
------
Four axes, each normalized to [0, 1], combined as a weighted sum:

1. x_height_compat   — closer x-height ratios pair better for mixed body text;
                        a heading and body font with very different x-heights
                        look visually mismatched when set at similar sizes.
2. category_contrast  — pairing across categories (serif+sans, slab+sans, ...)
                        reads as an intentional hierarchy choice; pairing two
                        fonts from the *same* category (esp. two serifs or two
                        display faces) tends to look like a mistake unless
                        they're clearly differentiated in weight/structure.
3. weight_compat      — some weight difference between heading/body helps
                        hierarchy read clearly, but an extreme difference (e.g.
                        Thin against Black) looks accidental rather than
                        designed. Scored as a curve peaking at a moderate gap.
4. stroke_contrast_similarity — pairing two faces with similar stroke-contrast
                        character (both high-contrast, or both low-contrast)
                        tends to look coherent; mixing a high-contrast serif
                        with a low-contrast slab, for instance, can clash.

Weights started equal (0.25 each) per the spec's guidance to begin uniform
and tune from validation (see validate.py / validation/known_pairings.json).
That baseline gave no clean separation between the known-good and known-bad
sets (margin 0.033, several bad pairings scoring as high as good ones) — a
grid search (src/tune_weights.py) over weight combinations found that
category_contrast is by far the strongest signal in this validation set
(same-category pairings, including "two similar grotesques" and "two
competing high-contrast serifs", are exactly the bad examples), so it was
weighted up to 0.50. The current weights below give clean separation: every
known-good pairing (avg 0.618, min 0.520) outscores every known-bad pairing
(avg 0.406, max 0.489). See validate.py's output for current numbers; rerun
tune_weights.py if the validation set grows enough to justify a new search.
"""

from dataclasses import dataclass, field

# Category compatibility matrix: how well two *categories* pair, independent
# of the specific fonts. 1.0 = classic, intentional-feeling contrast.
# 0.3-0.45 = same-category pairings, which can work but read as a bolder,
# riskier choice and more easily look like an error rather than a decision.
CATEGORY_COMPAT = {
    frozenset({"serif", "sans-serif"}): 1.0,
    frozenset({"slab-serif", "sans-serif"}): 0.9,
    frozenset({"serif", "slab-serif"}): 0.75,
    frozenset({"display", "serif"}): 0.85,
    frozenset({"display", "sans-serif"}): 0.85,
    frozenset({"display", "slab-serif"}): 0.7,
    frozenset({"monospace", "sans-serif"}): 0.8,
    frozenset({"monospace", "serif"}): 0.75,
    frozenset({"monospace", "slab-serif"}): 0.65,
    frozenset({"monospace", "display"}): 0.6,
    frozenset({"serif"}): 0.35,
    frozenset({"sans-serif"}): 0.4,
    frozenset({"slab-serif"}): 0.35,
    frozenset({"display"}): 0.3,
    frozenset({"monospace"}): 0.45,
}

WEIGHTS = {
    "x_height_compat": 0.20,
    "category_contrast": 0.50,
    "weight_compat": 0.20,
    "stroke_contrast_similarity": 0.10,
}


@dataclass
class PairScore:
    total: float
    axes: dict = field(default_factory=dict)
    explanation: str = ""


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_x_height(font_a: dict, font_b: dict) -> float:
    diff = abs(font_a["x_height_ratio"] - font_b["x_height_ratio"])
    return round(_clamp01(1 - diff / 0.15), 4)


def score_category(font_a: dict, font_b: dict) -> float:
    cat_a, cat_b = font_a["category"], font_b["category"]
    if cat_a == "unknown" or cat_b == "unknown":
        return 0.5
    key = frozenset({cat_a, cat_b})
    if key in CATEGORY_COMPAT:
        return CATEGORY_COMPAT[key]
    return 0.5


def score_weight(font_a: dict, font_b: dict) -> float:
    diff = abs(font_a["weight_class"] - font_b["weight_class"])
    ideal = 300.0
    spread = 300.0
    return round(_clamp01(1 - abs(diff - ideal) / spread), 4)


def score_stroke_contrast(font_a: dict, font_b: dict) -> float:
    diff = abs(font_a["stroke_contrast"] - font_b["stroke_contrast"])
    return round(_clamp01(1 - diff / 0.6), 4)


def score_pair(font_a: dict, font_b: dict) -> PairScore:
    """font_a / font_b are dict-like rows with the metrics columns produced by
    extract_metrics.py / build_database.py (family_name, category,
    x_height_ratio, weight_class, stroke_contrast, ...)."""
    axes = {
        "x_height_compat": score_x_height(font_a, font_b),
        "category_contrast": score_category(font_a, font_b),
        "weight_compat": score_weight(font_a, font_b),
        "stroke_contrast_similarity": score_stroke_contrast(font_a, font_b),
    }
    total = round(sum(axes[k] * WEIGHTS[k] for k in WEIGHTS), 4)
    explanation = _explain(font_a, font_b, axes)
    return PairScore(total=total, axes=axes, explanation=explanation)


def _explain(font_a: dict, font_b: dict, axes: dict) -> str:
    parts = []

    xdiff = abs(font_a["x_height_ratio"] - font_b["x_height_ratio"])
    if xdiff < 0.03:
        parts.append(
            f"Very similar x-height ({font_a['x_height_ratio']} vs {font_b['x_height_ratio']})"
        )
    elif xdiff < 0.08:
        parts.append(
            f"Shares similar x-height ({font_a['x_height_ratio']} vs {font_b['x_height_ratio']})"
        )
    else:
        parts.append(
            f"Noticeably different x-height ({font_a['x_height_ratio']} vs {font_b['x_height_ratio']})"
        )

    cat_a, cat_b = font_a["category"], font_b["category"]
    if cat_a == cat_b:
        parts.append(f"same category ({cat_a})")
    else:
        parts.append(f"contrasts in category ({cat_a} vs {cat_b})")

    wdiff = abs(font_a["weight_class"] - font_b["weight_class"])
    if wdiff < 100:
        parts.append(f"minimal weight difference ({font_a['weight_class']} vs {font_b['weight_class']})")
    elif wdiff < 400:
        parts.append(f"moderate weight difference ({font_a['weight_class']} vs {font_b['weight_class']})")
    else:
        parts.append(f"large weight difference ({font_a['weight_class']} vs {font_b['weight_class']})")

    cdiff = abs(font_a["stroke_contrast"] - font_b["stroke_contrast"])
    if cdiff < 0.15:
        parts.append("similar stroke contrast")
    else:
        parts.append("differing stroke contrast")

    return "; ".join(parts) + "."

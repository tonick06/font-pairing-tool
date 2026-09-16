import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from scoring import score_pair

SERIF_HIGH_CONTRAST = {
    "family_name": "TestSerif", "category": "serif",
    "x_height_ratio": 0.48, "weight_class": 400, "stroke_contrast": 0.35,
}
SANS_LOW_CONTRAST = {
    "family_name": "TestSans", "category": "sans-serif",
    "x_height_ratio": 0.52, "weight_class": 700, "stroke_contrast": 0.82,
}
ANOTHER_SERIF = {
    "family_name": "TestSerif2", "category": "serif",
    "x_height_ratio": 0.47, "weight_class": 420, "stroke_contrast": 0.33,
}


def test_score_pair_returns_axes_summing_to_total():
    result = score_pair(SERIF_HIGH_CONTRAST, SANS_LOW_CONTRAST)
    assert 0 <= result.total <= 1
    assert set(result.axes.keys()) == {
        "x_height_compat", "category_contrast", "weight_compat", "stroke_contrast_similarity"
    }


def test_cross_category_scores_higher_than_same_category_alone():
    from scoring import score_category
    cross = score_category(SERIF_HIGH_CONTRAST, SANS_LOW_CONTRAST)
    same = score_category(SERIF_HIGH_CONTRAST, ANOTHER_SERIF)
    assert cross > same


def test_identical_x_height_scores_max_on_that_axis():
    from scoring import score_x_height
    a = dict(SERIF_HIGH_CONTRAST)
    b = dict(SERIF_HIGH_CONTRAST)
    assert score_x_height(a, b) == 1.0


def test_explanation_is_nonempty_string():
    result = score_pair(SERIF_HIGH_CONTRAST, SANS_LOW_CONTRAST)
    assert isinstance(result.explanation, str)
    assert len(result.explanation) > 0

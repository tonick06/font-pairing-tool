import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from category_lookup import category_for, FAMILY_CATEGORY


def test_exact_match():
    assert category_for("Roboto") == "sans-serif"
    assert category_for("Georgia") == "serif"


def test_case_insensitive_fallback_match():
    assert category_for("roboto") == "sans-serif"
    assert category_for("PLAYFAIR DISPLAY") == "serif"


def test_unknown_family_returns_unknown():
    assert category_for("Definitely Not A Real Font Family") == "unknown"


def test_slab_serif_examples_are_true_low_contrast_slabs():
    for name in ["Roboto Slab", "Zilla Slab", "Arvo", "Aleo"]:
        assert FAMILY_CATEGORY[name] == "slab-serif"


def test_cycle16_recategorization_stuck():
    """Regression test: Trirong, Rosarivo, and Trocchi were moved from
    slab-serif to serif in cycle 16 after their measured stroke contrast
    (0.4-0.54) turned out to match old-style serifs, not true slabs."""
    for name in ["Trirong", "Rosarivo", "Trocchi"]:
        assert FAMILY_CATEGORY[name] == "serif"

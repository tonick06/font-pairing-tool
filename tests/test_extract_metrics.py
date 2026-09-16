import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from extract_metrics import extract_metrics

GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"
ROSARIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", "Rosarivo.ttf"
)


def test_georgia_is_high_contrast_serif():
    m = extract_metrics(GEORGIA)
    assert m.category == "serif"
    assert m.stroke_contrast < 0.6


def test_arial_is_low_contrast_sans():
    m = extract_metrics(ARIAL)
    assert m.category == "sans-serif"
    assert m.stroke_contrast > 0.6


def test_georgia_has_more_contrast_than_arial():
    georgia = extract_metrics(GEORGIA)
    arial = extract_metrics(ARIAL)
    assert georgia.stroke_contrast < arial.stroke_contrast


def test_ratios_are_normalized_to_units_per_em():
    m = extract_metrics(GEORGIA)
    assert 0 < m.x_height_ratio < 1
    assert 0 < m.cap_height_ratio < 1
    assert m.cap_height_ratio > m.x_height_ratio


@pytest.mark.skipif(not os.path.exists(ROSARIVO), reason="fonts/ not populated in this checkout")
def test_implausible_os2_xheight_falls_back_to_glyph_measurement():
    """Regression test for cycle 10: Rosarivo.ttf's own OS/2.sxHeight field
    is 170/1000 (ratio 0.17), well outside plausible typographic range, while
    its actual 'x' glyph outline measures ~509/1000 (ratio ~0.51). Extraction
    must not trust a present-but-implausible OS/2 value."""
    m = extract_metrics(ROSARIVO)
    assert 0.4 < m.x_height_ratio < 0.6

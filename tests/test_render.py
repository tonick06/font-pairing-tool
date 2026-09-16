import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from render import render_pairing


def test_render_pairing_creates_image(tmp_path):
    out_dir = str(tmp_path)
    path = render_pairing("Playfair Display", "Source Sans 3", out_dir=out_dir)
    assert os.path.exists(path)
    assert path.startswith(out_dir)
    assert path.endswith(".png")


def test_render_pairing_unknown_font_raises(tmp_path):
    try:
        render_pairing("Definitely Not A Real Font", "Source Sans 3", out_dir=str(tmp_path))
        assert False, "expected ValueError"
    except ValueError as e:
        assert "not found" in str(e)

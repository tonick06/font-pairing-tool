import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from compare_files import score_font_files

GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"


def test_scores_arbitrary_files_not_in_database():
    result = score_font_files(GEORGIA, ARIAL)
    assert result["font_a"] == "Georgia"
    assert result["font_b"] == "Arial"
    assert 0 <= result["score"] <= 1
    assert set(result["axes"].keys()) == {
        "x_height_compat", "category_contrast", "weight_compat", "stroke_contrast_similarity"
    }


def test_missing_file_raises_clear_error():
    try:
        score_font_files("C:/nonexistent/font.ttf", ARIAL)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "not found" in str(e)


def test_render_font_files_produces_image(tmp_path):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
    from render import render_font_files

    out_path = str(tmp_path / "test_compare.png")
    result = render_font_files(GEORGIA, ARIAL, out_path=out_path)
    assert os.path.exists(result["image_path"])
    assert result["image_path"] == out_path

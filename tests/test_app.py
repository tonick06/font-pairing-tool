import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from app import app

GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"


def _client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_lists_fonts_without_selection():
    resp = _client().get("/")
    assert resp.status_code == 200
    assert b"Choose a font" in resp.data


def test_index_shows_pairings_for_selected_font():
    resp = _client().get("/?font=Playfair+Display")
    assert resp.status_code == 200
    assert b"Top pairings for Playfair Display" in resp.data
    assert b"Score:" in resp.data


def test_upload_scores_two_valid_font_files():
    client = _client()
    with open(GEORGIA, "rb") as fa, open(ARIAL, "rb") as fb:
        resp = client.post(
            "/upload",
            data={"font_a": (fa, "georgia.ttf"), "font_b": (fb, "arial.ttf")},
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    assert b"Score:" in resp.data
    assert b"/output/uploads/" in resp.data


def test_upload_missing_files_shows_error():
    resp = _client().post("/upload", data={}, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert b"choose two font files" in resp.data


def test_upload_rejects_disallowed_extension():
    client = _client()
    with open(GEORGIA, "rb") as fa, open(ARIAL, "rb") as fb:
        resp = client.post(
            "/upload",
            data={"font_a": (fa, "georgia.txt"), "font_b": (fb, "arial.ttf")},
            content_type="multipart/form-data",
        )
    assert resp.status_code == 200
    assert b".ttf and .otf" in resp.data

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from app import app
import build_database

GEORGIA = "C:/Windows/Fonts/georgia.ttf"
ARIAL = "C:/Windows/Fonts/arial.ttf"


def _isolate_persistence(tmp_path, monkeypatch):
    """Redirect where uploaded fonts get persisted (fonts/ + metrics.db) to
    a throwaway temp location, so tests never mutate the real font library
    or database. build_database.FONTS_DIR/DB_PATH are read fresh inside
    persist_uploaded_font/add_font_to_database at call time (not bound as
    default parameter values), so monkeypatching the module attributes
    here actually takes effect."""
    monkeypatch.setattr(build_database, "FONTS_DIR", str(tmp_path / "fonts"))
    monkeypatch.setattr(build_database, "DB_PATH", str(tmp_path / "metrics.db"))


def _client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_shows_stats_and_nav():
    resp = _client().get("/")
    assert resp.status_code == 200
    assert b"Fonts" in resp.data
    assert b"Recommend" in resp.data
    assert b"Compare" in resp.data
    assert b"Browse" in resp.data


def test_recommend_page_lists_fonts_without_selection():
    resp = _client().get("/recommend")
    assert resp.status_code == 200
    assert b"<select" in resp.data


def test_recommend_page_shows_pairings_for_selected_font():
    resp = _client().get("/recommend?font=Playfair+Display")
    assert resp.status_code == 200
    assert b"Top pairings for Playfair Display" in resp.data
    assert b"Score:" in resp.data


def test_compare_page_renders_upload_form():
    resp = _client().get("/compare")
    assert resp.status_code == 200
    assert b'name="font_a"' in resp.data
    assert b'name="font_b"' in resp.data


def test_upload_scores_two_valid_font_files(tmp_path, monkeypatch):
    _isolate_persistence(tmp_path, monkeypatch)
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


def test_upload_persists_fonts_to_isolated_location_not_production(tmp_path, monkeypatch):
    """Regression test: an earlier version of this feature copied uploaded
    fonts straight into the real fonts/ dir and metrics.db as a side effect
    of running this very test suite."""
    _isolate_persistence(tmp_path, monkeypatch)
    client = _client()
    with open(GEORGIA, "rb") as fa, open(ARIAL, "rb") as fb:
        client.post(
            "/upload",
            data={"font_a": (fa, "georgia.ttf"), "font_b": (fb, "arial.ttf")},
            content_type="multipart/form-data",
        )
    assert (tmp_path / "fonts" / "Georgia.ttf").exists()
    assert (tmp_path / "fonts" / "Arial.ttf").exists()
    assert (tmp_path / "metrics.db").exists()


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


def test_match_font_finds_top_matches_from_database(tmp_path, monkeypatch):
    _isolate_persistence(tmp_path, monkeypatch)
    client = _client()
    with open(GEORGIA, "rb") as fa:
        resp = client.post(
            "/match", data={"font_solo": (fa, "georgia.ttf")}, content_type="multipart/form-data"
        )
    assert resp.status_code == 200
    assert b"Top matches for Georgia" in resp.data
    assert b"Score:" in resp.data


def test_match_font_missing_file_shows_error():
    resp = _client().post("/match", data={}, content_type="multipart/form-data")
    assert resp.status_code == 200
    assert b"choose a font file" in resp.data


def test_browse_page_lists_all_fonts():
    resp = _client().get("/browse")
    assert resp.status_code == 200
    assert b"Playfair Display" in resp.data


def test_browse_page_filters_by_category():
    resp = _client().get("/browse?category=monospace")
    assert resp.status_code == 200
    assert b"JetBrains Mono" in resp.data
    assert b"Playfair Display" not in resp.data


def test_about_page_shows_weights_and_validation_numbers():
    resp = _client().get("/about")
    assert resp.status_code == 200
    assert b"category_contrast" in resp.data
    assert b"Clean separation" not in resp.data  # prose page, not the raw validate.py output
    assert b"margin of" in resp.data

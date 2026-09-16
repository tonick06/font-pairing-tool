"""Score two arbitrary font files directly, with no requirement that either
be pre-loaded into the database. Reuses the same Milestone 1 extraction and
Milestone 3 scoring used everywhere else in the tool.
"""

import dataclasses
import os
import re
import shutil
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_metrics import extract_metrics
from scoring import score_pair
from recommend import DB_PATH, _connect
import build_database


def score_font_files(path_a: str, path_b: str) -> dict:
    if not os.path.isfile(path_a):
        raise ValueError(f"Font file not found: {path_a}")
    if not os.path.isfile(path_b):
        raise ValueError(f"Font file not found: {path_b}")

    metrics_a = dataclasses.asdict(extract_metrics(path_a))
    metrics_b = dataclasses.asdict(extract_metrics(path_b))
    result = score_pair(metrics_a, metrics_b)

    return {
        "font_a": metrics_a["family_name"],
        "font_b": metrics_b["family_name"],
        "path_a": path_a,
        "path_b": path_b,
        "score": result.total,
        "axes": result.axes,
        "explanation": result.explanation,
        "metrics_a": metrics_a,
        "metrics_b": metrics_b,
    }


def persist_uploaded_font(tmp_path: str, fonts_dir: str = None, db_path: str = None) -> dict:
    """Copy an uploaded font into the permanent fonts/ library and add it to
    the database, so it shows up in future Recommend/Browse results rather
    than existing only for the request that uploaded it.

    If a font with the same derived filename already exists (e.g. someone
    uploads a copy of a font already in the curated library), the existing
    library file and database row are left untouched - we never overwrite
    the curated collection with an upload.

    fonts_dir/db_path default to None (resolved from build_database's
    module attributes inside the function body) rather than binding
    build_database.FONTS_DIR/DB_PATH directly as default values, so tests
    can monkeypatch those attributes and have it actually take effect."""
    if fonts_dir is None:
        fonts_dir = build_database.FONTS_DIR
    if db_path is None:
        db_path = build_database.DB_PATH

    metrics = extract_metrics(tmp_path)
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "", metrics.family_name)
    if not safe_name:
        safe_name = "UploadedFont" + uuid.uuid4().hex[:6]
    dest_path = os.path.join(fonts_dir, f"{safe_name}.ttf")

    persisted = False
    if not os.path.exists(dest_path):
        os.makedirs(fonts_dir, exist_ok=True)
        shutil.copyfile(tmp_path, dest_path)
        build_database.add_font_to_database(dest_path, db_path=db_path)
        persisted = True

    return {
        "family_name": metrics.family_name,
        "filepath": dest_path,
        "persisted": persisted,
    }


def recommend_for_file(path: str, top_n: int = 5, db_path: str = DB_PATH) -> dict:
    """Score an uploaded font file against every font already in the
    database and return its top_n best matches, ranked highest first."""
    if not os.path.isfile(path):
        raise ValueError(f"Font file not found: {path}")

    target_metrics = dataclasses.asdict(extract_metrics(path))

    conn = _connect(db_path)
    fonts = [dict(row) for row in conn.execute("SELECT * FROM fonts").fetchall()]
    conn.close()

    matches = []
    for candidate in fonts:
        result = score_pair(target_metrics, candidate)
        matches.append({
            "family_name": candidate["family_name"],
            "category": candidate["category"],
            "filepath": candidate["filepath"],
            "score": result.total,
            "axes": result.axes,
            "explanation": result.explanation,
        })
    matches.sort(key=lambda m: m["score"], reverse=True)

    return {
        "uploaded_path": path,
        "uploaded_family": target_metrics["family_name"],
        "uploaded_category": target_metrics["category"],
        "matches": matches[:top_n],
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_files.py <font_a.ttf> <font_b.ttf>")
        sys.exit(1)
    result = score_font_files(sys.argv[1], sys.argv[2])
    print(f"{result['font_a']} + {result['font_b']}: {result['score']:.3f}")
    for axis, value in result["axes"].items():
        print(f"  {axis:28s} {value:.3f}")
    print(f"  {result['explanation']}")

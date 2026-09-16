"""Milestone 6 web UI, expanded into a full multi-page site: home,
recommend (pick a font, see top pairings), compare (upload two font
files, no database entry required), browse (filter the whole database),
and about (scoring methodology + validation numbers).

Run with:
    python app.py
then open http://127.0.0.1:5000
"""

import os
import sys
import uuid

from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from recommend import recommend_pairings, _connect, DB_PATH
from render import render_pairing, render_font_files, OUTPUT_DIR
from compare_files import recommend_for_file, persist_uploaded_font
from scoring import WEIGHTS
from validate import run_validation

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB, plenty for two font files

UPLOAD_DIR = os.path.join(OUTPUT_DIR, "uploads")
ALLOWED_EXTENSIONS = {".ttf", ".otf"}

AXIS_DESCRIPTIONS = {
    "x_height_compat": "Closer x-height ratios pair better for mixed body text at similar sizes",
    "category_contrast": "Serif+sans (etc.) reads as intentional hierarchy; same-category pairings score lower",
    "weight_compat": "Peaks at a moderate weight gap - enough for hierarchy, not so much it looks accidental",
    "stroke_contrast_similarity": "Two faces with similar stroke-contrast character tend to look coherent together",
}


def all_font_names():
    conn = _connect(DB_PATH)
    rows = conn.execute("SELECT DISTINCT family_name FROM fonts ORDER BY family_name").fetchall()
    conn.close()
    return [r[0] for r in rows]


def _allowed_font_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    conn = _connect(DB_PATH)
    total_fonts = conn.execute("SELECT COUNT(*) FROM fonts").fetchone()[0]
    category_counts = conn.execute(
        "SELECT category, COUNT(*) FROM fonts GROUP BY category ORDER BY COUNT(*) DESC"
    ).fetchall()
    conn.close()
    return render_template(
        "index.html", active="home", total_fonts=total_fonts, category_counts=category_counts
    )


@app.route("/recommend")
def recommend_page():
    fonts = all_font_names()
    selected = request.args.get("font")
    results = []
    if selected:
        recs = recommend_pairings(selected, top_n=5)
        for r in recs:
            image_path = render_pairing(selected, r["family_name"], out_dir=OUTPUT_DIR)
            results.append({
                "family_name": r["family_name"],
                "category": r["category"],
                "score": r["score"],
                "explanation": r["explanation"],
                "image": os.path.basename(image_path),
            })
    return render_template(
        "recommend.html", active="recommend", fonts=fonts, selected=selected, results=results
    )


@app.context_processor
def inject_total_fonts():
    conn = _connect(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM fonts").fetchone()[0]
    conn.close()
    return {"total_fonts": total}


@app.route("/compare")
def compare_page():
    return render_template("compare.html", active="compare")


@app.route("/upload", methods=["POST"])
def upload():
    file_a = request.files.get("font_a")
    file_b = request.files.get("font_b")

    error = None
    if not file_a or not file_a.filename or not file_b or not file_b.filename:
        error = "Please choose two font files."
    elif not (_allowed_font_file(file_a.filename) and _allowed_font_file(file_b.filename)):
        error = "Only .ttf and .otf files are accepted."

    if error:
        return render_template("compare.html", active="compare", upload_error=error)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    token = uuid.uuid4().hex[:8]
    name_a = f"{token}_a_{secure_filename(file_a.filename)}"
    name_b = f"{token}_b_{secure_filename(file_b.filename)}"
    path_a = os.path.join(UPLOAD_DIR, name_a)
    path_b = os.path.join(UPLOAD_DIR, name_b)
    file_a.save(path_a)
    file_b.save(path_b)

    try:
        # Persisting means this font shows up in future Recommend/Browse
        # results too, not just this one comparison.
        persisted_a = persist_uploaded_font(path_a)
        persisted_b = persist_uploaded_font(path_b)
        result = render_font_files(persisted_a["filepath"], persisted_b["filepath"], out_dir=UPLOAD_DIR)
    except Exception as e:
        return render_template(
            "compare.html", active="compare", upload_error=f"Could not score these fonts: {e}"
        )

    upload_result = {
        "score": result["score"],
        "explanation": result["explanation"],
        "image": os.path.basename(result["image_path"]),
    }
    return render_template("compare.html", active="compare", upload_result=upload_result)


@app.route("/match", methods=["POST"])
def match_font():
    file_a = request.files.get("font_solo")

    if not file_a or not file_a.filename:
        return render_template("compare.html", active="compare", match_error="Please choose a font file.")
    if not _allowed_font_file(file_a.filename):
        return render_template(
            "compare.html", active="compare", match_error="Only .ttf and .otf files are accepted."
        )

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    token = uuid.uuid4().hex[:8]
    path_a = os.path.join(UPLOAD_DIR, f"{token}_solo_{secure_filename(file_a.filename)}")
    file_a.save(path_a)

    try:
        # Rank against the database *before* persisting, so the just-uploaded
        # font can't match against itself.
        result = recommend_for_file(path_a, top_n=5)
        persisted_a = persist_uploaded_font(path_a)
    except Exception as e:
        return render_template(
            "compare.html", active="compare", match_error=f"Could not read this font: {e}"
        )

    matches = []
    for m in result["matches"]:
        rendered = render_font_files(persisted_a["filepath"], m["filepath"], out_dir=UPLOAD_DIR)
        matches.append({
            "family_name": m["family_name"],
            "category": m["category"],
            "score": m["score"],
            "explanation": m["explanation"],
            "image": os.path.basename(rendered["image_path"]),
        })

    return render_template(
        "compare.html", active="compare",
        match_uploaded_family=result["uploaded_family"], match_results=matches,
    )


@app.route("/browse")
def browse_page():
    conn = _connect(DB_PATH)
    categories = [r[0] for r in conn.execute(
        "SELECT DISTINCT category FROM fonts ORDER BY category"
    ).fetchall()]
    selected_category = request.args.get("category")
    query = "SELECT family_name, category, x_height_ratio, stroke_contrast FROM fonts"
    params = ()
    if selected_category:
        query += " WHERE category = ?"
        params = (selected_category,)
    query += " ORDER BY family_name"
    fonts = [dict(row) for row in conn.execute(query, params).fetchall()]
    conn.close()
    return render_template(
        "browse.html", active="browse", fonts=fonts, categories=categories,
        selected_category=selected_category,
    )


@app.route("/about")
def about_page():
    weights = [
        (axis, WEIGHTS[axis], AXIS_DESCRIPTIONS[axis])
        for axis in sorted(WEIGHTS, key=lambda a: -WEIGHTS[a])
    ]
    result = run_validation(verbose=False)
    pairing_count = len(result["good_scores"]) + len(result["bad_scores"]) if result else "?"
    margin = f"{result['margin']:.3f}" if result else "?"
    return render_template(
        "about.html", active="about", weights=weights, pairing_count=pairing_count, margin=margin
    )


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

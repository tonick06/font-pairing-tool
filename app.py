"""Milestone 6 (stretch): minimal web UI.

Pick a font from a dropdown, see its top pairing recommendations rendered
inline as sample images.

Run with:
    python app.py
then open http://127.0.0.1:5000
"""

import os
import sys
import uuid

from flask import Flask, render_template_string, request, send_from_directory
from werkzeug.utils import secure_filename

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from recommend import recommend_pairings, _connect, DB_PATH
from render import render_pairing, render_font_files, OUTPUT_DIR

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB, plenty for two font files

UPLOAD_DIR = os.path.join(OUTPUT_DIR, "uploads")
ALLOWED_EXTENSIONS = {".ttf", ".otf"}

PAGE = """
<!doctype html>
<html>
<head>
  <title>Font Pairing Tool</title>
  <style>
    html { background: #fff; color-scheme: light; }
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; color: #222; background: #fff; }
    h1 { font-size: 22px; }
    form { margin-bottom: 30px; }
    select, button { font-size: 15px; padding: 6px 10px; }
    .pairing { border: 1px solid #ddd; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
    .pairing img { max-width: 100%; border-radius: 4px; }
    .score { color: #666; font-size: 14px; margin-top: 8px; }
  </style>
</head>
<body>
  <h1>Font Pairing Tool</h1>
  <form method="get">
    <label for="font">Choose a font:</label>
    <select name="font" id="font">
      {% for f in fonts %}
        <option value="{{ f }}" {% if f == selected %}selected{% endif %}>{{ f }}</option>
      {% endfor %}
    </select>
    <button type="submit">Show pairings</button>
  </form>

  {% if selected %}
    <h2>Top pairings for {{ selected }}</h2>
    {% for r in results %}
      <div class="pairing">
        <img src="/output/{{ r.image }}">
        <div class="score">Score: {{ "%.2f"|format(r.score) }} — {{ r.explanation }}</div>
      </div>
    {% endfor %}
  {% endif %}

  <hr style="margin: 40px 0; border: none; border-top: 1px solid #ddd;">

  <h1>Or upload your own two fonts</h1>
  <form method="post" action="/upload" enctype="multipart/form-data">
    <p><label>Font A (heading): <input type="file" name="font_a" accept=".ttf,.otf" required></label></p>
    <p><label>Font B (body): <input type="file" name="font_b" accept=".ttf,.otf" required></label></p>
    <button type="submit">Score this pairing</button>
  </form>

  {% if upload_error %}
    <p style="color: #b00020;">{{ upload_error }}</p>
  {% endif %}

  {% if upload_result %}
    <div class="pairing">
      <img src="/output/uploads/{{ upload_result.image }}">
      <div class="score">Score: {{ "%.2f"|format(upload_result.score) }} — {{ upload_result.explanation }}</div>
    </div>
  {% endif %}
</body>
</html>
"""


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
    fonts = all_font_names()
    selected = request.args.get("font")
    results = []
    if selected:
        recs = recommend_pairings(selected, top_n=5)
        for r in recs:
            image_path = render_pairing(selected, r["family_name"], out_dir=OUTPUT_DIR)
            results.append({
                "family_name": r["family_name"],
                "score": r["score"],
                "explanation": r["explanation"],
                "image": os.path.basename(image_path),
            })
    return render_template_string(PAGE, fonts=fonts, selected=selected, results=results)


@app.route("/upload", methods=["POST"])
def upload():
    fonts = all_font_names()
    file_a = request.files.get("font_a")
    file_b = request.files.get("font_b")

    error = None
    if not file_a or not file_a.filename or not file_b or not file_b.filename:
        error = "Please choose two font files."
    elif not (_allowed_font_file(file_a.filename) and _allowed_font_file(file_b.filename)):
        error = "Only .ttf and .otf files are accepted."

    if error:
        return render_template_string(PAGE, fonts=fonts, selected=None, results=[], upload_error=error)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    token = uuid.uuid4().hex[:8]
    name_a = f"{token}_a_{secure_filename(file_a.filename)}"
    name_b = f"{token}_b_{secure_filename(file_b.filename)}"
    path_a = os.path.join(UPLOAD_DIR, name_a)
    path_b = os.path.join(UPLOAD_DIR, name_b)
    file_a.save(path_a)
    file_b.save(path_b)

    try:
        result = render_font_files(path_a, path_b, out_dir=UPLOAD_DIR)
    except Exception as e:
        return render_template_string(
            PAGE, fonts=fonts, selected=None, results=[],
            upload_error=f"Could not score these fonts: {e}",
        )

    upload_result = {
        "score": result["score"],
        "explanation": result["explanation"],
        "image": os.path.basename(result["image_path"]),
    }
    return render_template_string(PAGE, fonts=fonts, selected=None, results=[], upload_result=upload_result)


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

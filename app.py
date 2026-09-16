"""Milestone 6 (stretch): minimal web UI.

Pick a font from a dropdown, see its top pairing recommendations rendered
inline as sample images.

Run with:
    python app.py
then open http://127.0.0.1:5000
"""

import os
import sys

from flask import Flask, render_template_string, request, send_from_directory

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from recommend import recommend_pairings, _connect, DB_PATH
from render import render_pairing, OUTPUT_DIR

app = Flask(__name__)

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
</body>
</html>
"""


def all_font_names():
    conn = _connect(DB_PATH)
    rows = conn.execute("SELECT DISTINCT family_name FROM fonts ORDER BY family_name").fetchall()
    conn.close()
    return [r[0] for r in rows]


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


@app.route("/output/<path:filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

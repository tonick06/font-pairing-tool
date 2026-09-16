"""Milestone 2 (steps 2-4): run the Milestone 1 extractor across every font in
fonts/ and store the results in a SQLite database at data/metrics.db.

Failures (missing tables, corrupt files, unreadable glyphs) are logged and
skipped rather than crashing the whole run.
"""

import glob
import os
import sqlite3
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_metrics import extract_metrics

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS fonts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    family_name TEXT NOT NULL,
    subfamily_name TEXT,
    filepath TEXT UNIQUE NOT NULL,
    category TEXT,
    units_per_em INTEGER,
    weight_class INTEGER,
    width_class INTEGER,
    ascender REAL,
    descender REAL,
    x_height REAL,
    cap_height REAL,
    x_height_ratio REAL,
    cap_height_ratio REAL,
    ascender_ratio REAL,
    descender_ratio REAL,
    stroke_contrast REAL
);
"""


def add_font_to_database(filepath: str, db_path: str = None):
    """Upsert a single font's metrics into the database without touching any
    other rows. Used to persist a user-uploaded font (see app.py) so it
    shows up in future Recommend/Browse results, not just the one request
    that uploaded it. Unlike build_database(), does not drop the table.

    db_path defaults to None (resolved to the module-level DB_PATH inside
    the function body) rather than DB_PATH directly, so tests can
    monkeypatch build_database.DB_PATH and have it actually take effect -
    a default *value* is bound once at def time and won't see later
    reassignment of the module global otherwise."""
    if db_path is None:
        db_path = DB_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    m = extract_metrics(filepath)
    conn.execute(
        """INSERT OR REPLACE INTO fonts
           (family_name, subfamily_name, filepath, category, units_per_em,
            weight_class, width_class, ascender, descender, x_height,
            cap_height, x_height_ratio, cap_height_ratio, ascender_ratio,
            descender_ratio, stroke_contrast)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (m.family_name, m.subfamily_name, m.filepath, m.category,
         m.units_per_em, m.weight_class, m.width_class, m.ascender,
         m.descender, m.x_height, m.cap_height, m.x_height_ratio,
         m.cap_height_ratio, m.ascender_ratio, m.descender_ratio,
         m.stroke_contrast),
    )
    conn.commit()
    conn.close()
    return m


def build_database(fonts_dir: str = FONTS_DIR, db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE IF EXISTS fonts")
    conn.executescript(SCHEMA)

    font_paths = sorted(glob.glob(os.path.join(fonts_dir, "*.ttf")) +
                         glob.glob(os.path.join(fonts_dir, "*.otf")))

    ok, failed = 0, []
    for path in font_paths:
        try:
            m = extract_metrics(path)
            conn.execute(
                """INSERT OR REPLACE INTO fonts
                   (family_name, subfamily_name, filepath, category, units_per_em,
                    weight_class, width_class, ascender, descender, x_height,
                    cap_height, x_height_ratio, cap_height_ratio, ascender_ratio,
                    descender_ratio, stroke_contrast)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (m.family_name, m.subfamily_name, m.filepath, m.category,
                 m.units_per_em, m.weight_class, m.width_class, m.ascender,
                 m.descender, m.x_height, m.cap_height, m.x_height_ratio,
                 m.cap_height_ratio, m.ascender_ratio, m.descender_ratio,
                 m.stroke_contrast),
            )
            ok += 1
        except Exception as e:
            failed.append((path, str(e)))
            print(f"SKIP {os.path.basename(path)}: {e}")

    conn.commit()

    unknown_category = conn.execute(
        "SELECT family_name FROM fonts WHERE category = 'unknown'"
    ).fetchall()
    conn.close()

    print(f"\nBuilt database: {ok} fonts stored, {len(failed)} skipped -> {db_path}")
    if unknown_category:
        print(f"{len(unknown_category)} fonts have unknown category (add to category_lookup.py):")
        for row in unknown_category:
            print(f"  {row[0]}")
    return ok, failed


if __name__ == "__main__":
    build_database()

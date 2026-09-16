"""Milestone 4: recommendation API built on top of the Milestone 3 scoring function."""

import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring import score_pair

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.db")


def _connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _all_fonts(conn):
    return [dict(row) for row in conn.execute("SELECT * FROM fonts").fetchall()]


def get_font(name: str, db_path: str = DB_PATH):
    conn = _connect(db_path)
    row = conn.execute("SELECT * FROM fonts WHERE family_name = ? LIMIT 1", (name,)).fetchone()
    conn.close()
    return dict(row) if row else None


def recommend_pairings(font_name: str, top_n: int = 5, db_path: str = DB_PATH):
    """Return the top_n best-matching fonts for font_name, ranked by score."""
    conn = _connect(db_path)
    fonts = _all_fonts(conn)
    conn.close()

    target = next((f for f in fonts if f["family_name"].lower() == font_name.lower()), None)
    if target is None:
        raise ValueError(f"Font '{font_name}' not found in database")

    results = []
    for candidate in fonts:
        if candidate["family_name"] == target["family_name"]:
            continue
        result = score_pair(target, candidate)
        results.append({
            "family_name": candidate["family_name"],
            "category": candidate["category"],
            "score": result.total,
            "axes": result.axes,
            "explanation": result.explanation,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]


def score_pairing(font_a_name: str, font_b_name: str, db_path: str = DB_PATH):
    """Score a specific pair of fonts by name, with breakdown and explanation."""
    font_a = get_font(font_a_name, db_path)
    font_b = get_font(font_b_name, db_path)
    if font_a is None:
        raise ValueError(f"Font '{font_a_name}' not found in database")
    if font_b is None:
        raise ValueError(f"Font '{font_b_name}' not found in database")
    result = score_pair(font_a, font_b)
    return {
        "font_a": font_a["family_name"],
        "font_b": font_b["family_name"],
        "score": result.total,
        "axes": result.axes,
        "explanation": result.explanation,
    }


def main():
    if len(sys.argv) == 2:
        font_name = sys.argv[1]
        recs = recommend_pairings(font_name, top_n=5)
        print(f"Top pairings for {font_name}:")
        for r in recs:
            print(f"  {r['score']:.3f}  {r['family_name']:25s} ({r['category']})  {r['explanation']}")
    elif len(sys.argv) == 3:
        result = score_pairing(sys.argv[1], sys.argv[2])
        print(f"{result['font_a']} + {result['font_b']}: {result['score']:.3f}")
        print(f"  axes: {result['axes']}")
        print(f"  {result['explanation']}")
    else:
        print("Usage:\n  python recommend.py <font_name>\n  python recommend.py <font_a> <font_b>")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Milestone 3.1: validate the scoring function against known-good and
known-bad pairings, and report whether it separates them with a clear margin.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scoring import score_pair

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.db")
VALIDATION_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "validation", "known_pairings.json"
)


def _load_font(conn, family_name):
    row = conn.execute(
        "SELECT * FROM fonts WHERE family_name = ? LIMIT 1", (family_name,)
    ).fetchone()
    if row is None:
        return None
    cols = [d[0] for d in conn.execute("SELECT * FROM fonts LIMIT 0").description]
    return dict(zip(cols, row))


def run_validation(db_path: str = DB_PATH, validation_path: str = VALIDATION_PATH, verbose: bool = True):
    conn = sqlite3.connect(db_path)
    with open(validation_path) as f:
        data = json.load(f)

    def score_set(pairs, label):
        scores = []
        for a_name, b_name in pairs:
            font_a = _load_font(conn, a_name)
            font_b = _load_font(conn, b_name)
            if not font_a or not font_b:
                missing = a_name if not font_a else b_name
                if verbose:
                    print(f"  [skip] {a_name} / {b_name}: '{missing}' not in database")
                continue
            result = score_pair(font_a, font_b)
            scores.append(result.total)
            if verbose:
                print(f"  {result.total:.3f}  {a_name} + {b_name}  ({result.explanation})")
        return scores

    print(f"\n=== Known-GOOD pairings ===")
    good_scores = score_set(data["good_pairings"], "good")
    print(f"\n=== Known-BAD pairings ===")
    bad_scores = score_set(data["bad_pairings"], "bad")

    conn.close()

    if not good_scores or not bad_scores:
        print("\nNot enough matched fonts in the database to validate. Download more fonts first.")
        return None

    good_avg = sum(good_scores) / len(good_scores)
    bad_avg = sum(bad_scores) / len(bad_scores)
    good_min = min(good_scores)
    bad_max = max(bad_scores)
    margin = good_avg - bad_avg

    print(f"\nGood avg: {good_avg:.3f} (min {good_min:.3f})")
    print(f"Bad avg:  {bad_avg:.3f} (max {bad_max:.3f})")
    print(f"Margin (good_avg - bad_avg): {margin:.3f}")
    if good_min > bad_max:
        print("Clean separation: every good pairing outscores every bad pairing.")
    else:
        print("No clean separation - some bad pairings score as high as some good ones.")

    return {
        "good_scores": good_scores,
        "bad_scores": bad_scores,
        "good_avg": good_avg,
        "bad_avg": bad_avg,
        "margin": margin,
        "clean_separation": good_min > bad_max,
    }


if __name__ == "__main__":
    run_validation()

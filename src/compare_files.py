"""Score two arbitrary font files directly, with no requirement that either
be pre-loaded into the database. Reuses the same Milestone 1 extraction and
Milestone 3 scoring used everywhere else in the tool.
"""

import dataclasses
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_metrics import extract_metrics
from scoring import score_pair


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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_files.py <font_a.ttf> <font_b.ttf>")
        sys.exit(1)
    result = score_font_files(sys.argv[1], sys.argv[2])
    print(f"{result['font_a']} + {result['font_b']}: {result['score']:.3f}")
    for axis, value in result["axes"].items():
        print(f"  {axis:28s} {value:.3f}")
    print(f"  {result['explanation']}")

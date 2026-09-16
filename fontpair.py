"""EVOLUTION_LOG cycle 2: command-line interface for the font-pairing tool.

Usage:
    python fontpair.py recommend "Playfair Display" [--top 5]
    python fontpair.py score "Playfair Display" "Source Sans 3"
    python fontpair.py render "Playfair Display" "Source Sans 3" [--out output/]
    python fontpair.py list [--category serif]
    python fontpair.py compare path/to/fontA.ttf path/to/fontB.ttf [--render]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from recommend import recommend_pairings, score_pairing, _connect, DB_PATH
from render import render_pairing, render_font_files, OUTPUT_DIR
from compare_files import score_font_files


def cmd_recommend(args):
    try:
        recs = recommend_pairings(args.font, top_n=args.top)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Top {len(recs)} pairings for {args.font}:")
    for r in recs:
        print(f"  {r['score']:.3f}  {r['family_name']:25s} ({r['category']})")
        print(f"           {r['explanation']}")


def cmd_score(args):
    try:
        result = score_pairing(args.font_a, args.font_b)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"{result['font_a']} + {result['font_b']}: {result['score']:.3f}")
    for axis, value in result["axes"].items():
        print(f"  {axis:28s} {value:.3f}")
    print(f"  {result['explanation']}")


def cmd_render(args):
    try:
        path = render_pairing(args.font_a, args.font_b, out_dir=args.out)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"Rendered {path}")


def cmd_compare(args):
    try:
        if args.render:
            result = render_font_files(args.file_a, args.file_b, out_dir=args.out)
        else:
            result = score_font_files(args.file_a, args.file_b)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"{result['font_a']} + {result['font_b']}: {result['score']:.3f}")
    for axis, value in result["axes"].items():
        print(f"  {axis:28s} {value:.3f}")
    print(f"  {result['explanation']}")
    if args.render:
        print(f"Rendered {result['image_path']}")


def cmd_list(args):
    conn = _connect(DB_PATH)
    query = "SELECT family_name, category, x_height_ratio, stroke_contrast FROM fonts"
    params = ()
    if args.category:
        query += " WHERE category = ?"
        params = (args.category,)
    query += " ORDER BY category, family_name"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    if not rows:
        print("No fonts found.")
        return
    for row in rows:
        print(f"  {row['family_name']:25s} {row['category']:12s} "
              f"x-height={row['x_height_ratio']:.3f}  contrast={row['stroke_contrast']:.3f}")
    print(f"\n{len(rows)} fonts.")


def main():
    parser = argparse.ArgumentParser(prog="fontpair", description="Font pairing analysis CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_rec = sub.add_parser("recommend", help="Rank the database against a font")
    p_rec.add_argument("font")
    p_rec.add_argument("--top", type=int, default=5)
    p_rec.set_defaults(func=cmd_recommend)

    p_score = sub.add_parser("score", help="Score a specific pair of fonts")
    p_score.add_argument("font_a")
    p_score.add_argument("font_b")
    p_score.set_defaults(func=cmd_score)

    p_render = sub.add_parser("render", help="Render a demo image for a pairing")
    p_render.add_argument("font_a")
    p_render.add_argument("font_b")
    p_render.add_argument("--out", default=OUTPUT_DIR)
    p_render.set_defaults(func=cmd_render)

    p_compare = sub.add_parser("compare", help="Score two font files directly, no database required")
    p_compare.add_argument("file_a")
    p_compare.add_argument("file_b")
    p_compare.add_argument("--render", action="store_true", help="Also render a demo image")
    p_compare.add_argument("--out", default=OUTPUT_DIR)
    p_compare.set_defaults(func=cmd_compare)

    p_list = sub.add_parser("list", help="List fonts in the database")
    p_list.add_argument("--category", default=None)
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

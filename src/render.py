"""Milestone 5: render a heading (font A) + body paragraph (font B) sample
image for a given pairing, for demo/portfolio purposes.
"""

import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recommend import get_font, score_pairing

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")

HEADING_TEXT = "Design with Intention"
BODY_TEXT = (
    "Typography is the craft of giving language a visual form. A well-chosen "
    "pairing creates hierarchy without shouting, guiding the reader's eye from "
    "headline to body with a rhythm that feels inevitable rather than accidental."
)

WIDTH = 1000
MARGIN = 60
BG_COLOR = (255, 255, 255)
TEXT_COLOR = (20, 20, 20)
META_COLOR = (120, 120, 120)


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_pairing(font_a_name: str, font_b_name: str, out_dir: str = OUTPUT_DIR, db_path=None):
    kwargs = {"db_path": db_path} if db_path else {}
    font_a = get_font(font_a_name, **kwargs) if db_path else get_font(font_a_name)
    font_b = get_font(font_b_name, **kwargs) if db_path else get_font(font_b_name)
    if not font_a:
        raise ValueError(f"Font '{font_a_name}' not found in database")
    if not font_b:
        raise ValueError(f"Font '{font_b_name}' not found in database")

    score_info = score_pairing(font_a_name, font_b_name, **(kwargs if db_path else {}))

    heading_font = ImageFont.truetype(font_a["filepath"], 48)
    body_font = ImageFont.truetype(font_b["filepath"], 20)
    meta_font_path = font_b["filepath"]
    meta_font = ImageFont.truetype(meta_font_path, 14)

    scratch_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(scratch_img)

    content_width = WIDTH - MARGIN * 2
    body_lines = _wrap_text(draw, BODY_TEXT, body_font, content_width)

    heading_h = 70
    body_line_h = 30
    body_h = body_line_h * len(body_lines)
    meta_h = 50
    height = MARGIN + heading_h + 20 + body_h + 30 + meta_h + MARGIN

    img = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    draw.text((MARGIN, y), HEADING_TEXT, font=heading_font, fill=TEXT_COLOR)
    y += heading_h + 20

    for line in body_lines:
        draw.text((MARGIN, y), line, font=body_font, fill=TEXT_COLOR)
        y += body_line_h

    y += 20
    draw.line((MARGIN, y, WIDTH - MARGIN, y), fill=(220, 220, 220), width=1)
    y += 15
    meta_line1 = f"Heading: {font_a['family_name']}   |   Body: {font_b['family_name']}"
    meta_line2 = f"Compatibility score: {score_info['score']:.2f}   —   {score_info['explanation']}"
    draw.text((MARGIN, y), meta_line1, font=meta_font, fill=META_COLOR)
    draw.text((MARGIN, y + 20), meta_line2, font=meta_font, fill=META_COLOR)

    os.makedirs(out_dir, exist_ok=True)
    safe_a = re.sub(r"[^a-zA-Z0-9]+", "", font_a_name).lower()
    safe_b = re.sub(r"[^a-zA-Z0-9]+", "", font_b_name).lower()
    out_path = os.path.join(out_dir, f"pairing_{safe_a}_{safe_b}.png")
    img.save(out_path)
    return out_path


def render_top_pairings_for(font_name: str, top_n: int = 5, out_dir: str = OUTPUT_DIR):
    from recommend import recommend_pairings
    recs = recommend_pairings(font_name, top_n=top_n)
    paths = []
    for r in recs:
        path = render_pairing(font_name, r["family_name"], out_dir=out_dir)
        paths.append(path)
        print(f"Rendered {path}")
    return paths


def main():
    if len(sys.argv) != 3:
        print("Usage: python render.py <font_a> <font_b>")
        sys.exit(1)
    path = render_pairing(sys.argv[1], sys.argv[2])
    print(f"Rendered {path}")


if __name__ == "__main__":
    main()

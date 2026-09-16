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
SUBHEADING_TEXT = "A closer look at hierarchy"
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

HEADING_SIZE = 48
SUBHEADING_SIZE = 26
BODY_SIZE = 20


def _load_font(filepath: str, family_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font at a given size, raising a clear error naming the font and
    file instead of letting a bare Pillow/fontTools traceback surface."""
    try:
        return ImageFont.truetype(filepath, size)
    except Exception as e:
        raise ValueError(
            f"Could not render '{family_name}' ({filepath}) at size {size}: {e}"
        ) from e


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


def _render_from_metadata(font_a: dict, font_b: dict, score_info: dict, out_path: str) -> str:
    """Shared rendering core: font_a/font_b need 'filepath' and 'family_name';
    score_info needs 'score' and 'explanation'. Used by both the
    database-backed render_pairing and the file-based render_font_files."""
    heading_font = _load_font(font_a["filepath"], font_a["family_name"], HEADING_SIZE)
    subheading_font = _load_font(font_a["filepath"], font_a["family_name"], SUBHEADING_SIZE)
    body_font = _load_font(font_b["filepath"], font_b["family_name"], BODY_SIZE)
    meta_font = _load_font(font_b["filepath"], font_b["family_name"], 14)

    scratch_img = Image.new("RGB", (10, 10))
    draw = ImageDraw.Draw(scratch_img)

    content_width = WIDTH - MARGIN * 2
    body_lines = _wrap_text(draw, BODY_TEXT, body_font, content_width)

    meta_line1 = f"Heading: {font_a['family_name']}   |   Body: {font_b['family_name']}"
    meta_line2 = f"Compatibility score: {score_info['score']:.2f}   —   {score_info['explanation']}"
    meta_line2_wrapped = _wrap_text(draw, meta_line2, meta_font, content_width)

    heading_h = 70
    subheading_h = 40
    body_line_h = 30
    body_h = body_line_h * len(body_lines)
    meta_line_h = 20
    meta_h = meta_line_h * (1 + len(meta_line2_wrapped))
    height = MARGIN + heading_h + subheading_h + 10 + body_h + 30 + meta_h + MARGIN

    img = Image.new("RGB", (WIDTH, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    y = MARGIN
    draw.text((MARGIN, y), HEADING_TEXT, font=heading_font, fill=TEXT_COLOR)
    y += heading_h

    # A second, smaller heading size shows how the pairing holds up at a
    # scale closer to a section heading rather than only a hero headline.
    draw.text((MARGIN, y), SUBHEADING_TEXT, font=subheading_font, fill=TEXT_COLOR)
    y += subheading_h + 10

    for line in body_lines:
        draw.text((MARGIN, y), line, font=body_font, fill=TEXT_COLOR)
        y += body_line_h

    y += 20
    draw.line((MARGIN, y, WIDTH - MARGIN, y), fill=(220, 220, 220), width=1)
    y += 15
    draw.text((MARGIN, y), meta_line1, font=meta_font, fill=META_COLOR)
    y += meta_line_h
    for line in meta_line2_wrapped:
        draw.text((MARGIN, y), line, font=meta_font, fill=META_COLOR)
        y += meta_line_h

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    img.save(out_path)
    return out_path


def render_pairing(font_a_name: str, font_b_name: str, out_dir: str = OUTPUT_DIR, db_path=None):
    kwargs = {"db_path": db_path} if db_path else {}
    font_a = get_font(font_a_name, **kwargs) if db_path else get_font(font_a_name)
    font_b = get_font(font_b_name, **kwargs) if db_path else get_font(font_b_name)
    if not font_a:
        raise ValueError(f"Font '{font_a_name}' not found in database")
    if not font_b:
        raise ValueError(f"Font '{font_b_name}' not found in database")

    score_info = score_pairing(font_a_name, font_b_name, **(kwargs if db_path else {}))

    safe_a = re.sub(r"[^a-zA-Z0-9]+", "", font_a_name).lower()
    safe_b = re.sub(r"[^a-zA-Z0-9]+", "", font_b_name).lower()
    out_path = os.path.join(out_dir, f"pairing_{safe_a}_{safe_b}.png")
    return _render_from_metadata(font_a, font_b, score_info, out_path)


def render_font_files(path_a: str, path_b: str, out_dir: str = OUTPUT_DIR, out_path: str = None) -> dict:
    """Score and render a pairing directly from two font files, with no
    requirement that either be in the database. Returns a dict with the
    rendered image path plus the same score/axes/explanation shape as
    recommend.score_pairing."""
    from compare_files import score_font_files

    result = score_font_files(path_a, path_b)
    font_a = {"filepath": path_a, "family_name": result["font_a"]}
    font_b = {"filepath": path_b, "family_name": result["font_b"]}

    if out_path is None:
        safe_a = re.sub(r"[^a-zA-Z0-9]+", "", result["font_a"]).lower()
        safe_b = re.sub(r"[^a-zA-Z0-9]+", "", result["font_b"]).lower()
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"compare_{safe_a}_{safe_b}.png")

    image_path = _render_from_metadata(font_a, font_b, result, out_path)
    result["image_path"] = image_path
    return result


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

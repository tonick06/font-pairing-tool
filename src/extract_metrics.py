"""Milestone 1: extract structural typographic metrics from a single font file.

Usage:
    python extract_metrics.py path/to/font.ttf
"""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass, asdict

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from category_lookup import category_for


@dataclass
class FontMetrics:
    family_name: str
    subfamily_name: str
    filepath: str
    category: str
    units_per_em: int
    weight_class: int
    width_class: int
    ascender: float
    descender: float
    x_height: float
    cap_height: float
    x_height_ratio: float      # x-height / units_per_em
    cap_height_ratio: float    # cap-height / units_per_em
    ascender_ratio: float
    descender_ratio: float
    stroke_contrast: float     # thin-stroke / thick-stroke on glyph 'O'; lower = more contrast


def _get_name(ttfont: TTFont, name_id: int) -> str:
    name_table = ttfont["name"]
    rec = name_table.getName(name_id, 3, 1, 0x409) or name_table.getName(name_id, 1, 0, 0)
    if rec is None:
        for r in name_table.names:
            if r.nameID == name_id:
                return r.toUnicode()
        return ""
    return rec.toUnicode()


def _glyph_bbox(ttfont: TTFont, char: str):
    """Return (xMin, yMin, xMax, yMax) for a single character's glyph outline, or None."""
    cmap = ttfont.getBestCmap()
    codepoint = ord(char)
    if codepoint not in cmap:
        return None
    glyph_name = cmap[codepoint]
    glyph_set = ttfont.getGlyphSet()
    pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    return pen.bounds  # None if glyph has no outline (e.g. space)


def _measure_stroke_contrast(font_path: str, render_size: int = 400) -> float:
    """Approximate stroke contrast by rendering glyph 'O' and comparing the
    vertical stroke run at its horizontal center (thin axis, for most serif/sans
    letterforms) against the horizontal stroke run at its vertical center
    (thick axis). Returns thin/thick in [0, 1]; lower means higher contrast.
    Returns 1.0 (no measurable contrast) if the glyph can't be rendered.
    """
    try:
        pil_font = ImageFont.truetype(font_path, render_size)
    except Exception:
        return 1.0

    bbox = pil_font.getbbox("O")
    if bbox is None:
        return 1.0
    left, top, right, bottom = bbox
    w = right - left
    h = bottom - top
    if w <= 0 or h <= 0:
        return 1.0

    pad = 10
    img = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    draw = ImageDraw.Draw(img)
    draw.text((pad - left, pad - top), "O", font=pil_font, fill=255)
    pixels = img.load()
    img_w, img_h = img.size

    cx = pad - left + (left + right) // 2
    cy = pad - top + (top + bottom) // 2

    def vertical_run_at(x):
        """Longest contiguous filled run scanning down column x (captures top-stroke thickness)."""
        if x < 0 or x >= img_w:
            return None
        col = [1 if pixels[x, y] > 127 else 0 for y in range(img_h)]
        return _longest_run(col)

    def horizontal_run_at(y):
        if y < 0 or y >= img_h:
            return None
        row = [1 if pixels[x, y] > 127 else 0 for x in range(img_w)]
        return _longest_run(row)

    top_run = vertical_run_at(cx)
    side_run = horizontal_run_at(cy)

    if not top_run or not side_run or side_run == 0:
        return 1.0

    thin, thick = min(top_run, side_run), max(top_run, side_run)
    if thick == 0:
        return 1.0
    return round(thin / thick, 4)


def _longest_run(binary_seq):
    """Length of the longest run of 1s that is bounded by 0s on both sides
    (i.e. a stroke crossing, not the run touching the array edge)."""
    runs = []
    current = 0
    started_at_edge = True
    for i, v in enumerate(binary_seq):
        if v:
            current += 1
        else:
            if current > 0:
                ended_at_edge = False
                runs.append((current, started_at_edge, ended_at_edge))
            current = 0
            started_at_edge = False
    if current > 0:
        runs.append((current, started_at_edge, True))
    bounded = [r[0] for r in runs if not (r[1] and r[2])]
    candidates = bounded if bounded else [r[0] for r in runs]
    return max(candidates) if candidates else 0


def extract_metrics(font_path: str) -> FontMetrics:
    ttfont = TTFont(font_path, lazy=True)

    units_per_em = ttfont["head"].unitsPerEm
    hhea = ttfont["hhea"]
    ascender = hhea.ascender
    descender = hhea.descender

    os2 = ttfont["OS/2"] if "OS/2" in ttfont else None
    weight_class = os2.usWeightClass if os2 else 400
    width_class = os2.usWidthClass if os2 else 5

    x_height = getattr(os2, "sxHeight", 0) if os2 else 0
    cap_height = getattr(os2, "sCapHeight", 0) if os2 else 0

    # OS/2 sxHeight/sCapHeight are sometimes present but wrong (bad metadata
    # from the font's own authoring tool, not a parsing issue on our end -
    # e.g. Rosarivo.ttf ships sxHeight=170/1000 when its 'x' glyph outline
    # actually measures ~509/1000). Re-measure from the glyph outline
    # whenever the OS/2 value is missing OR outside a plausible typographic
    # range, rather than trusting a present-but-wrong value.
    x_height_ratio_prelim = (x_height / units_per_em) if x_height else 0
    if not (0.25 <= x_height_ratio_prelim <= 0.7):
        bbox = _glyph_bbox(ttfont, "x")
        x_height = bbox[3] if bbox else units_per_em * 0.5

    cap_height_ratio_prelim = (cap_height / units_per_em) if cap_height else 0
    if not (0.5 <= cap_height_ratio_prelim <= 0.9):
        bbox = _glyph_bbox(ttfont, "H")
        cap_height = bbox[3] if bbox else units_per_em * 0.7

    family_name = _get_name(ttfont, 1) or _get_name(ttfont, 16) or os.path.basename(font_path)
    subfamily_name = _get_name(ttfont, 2) or _get_name(ttfont, 17) or "Regular"
    typographic_family = _get_name(ttfont, 16) or family_name

    stroke_contrast = _measure_stroke_contrast(font_path)
    category = category_for(typographic_family)

    return FontMetrics(
        family_name=typographic_family,
        subfamily_name=subfamily_name,
        filepath=font_path,
        category=category,
        units_per_em=units_per_em,
        weight_class=weight_class,
        width_class=width_class,
        ascender=ascender,
        descender=descender,
        x_height=x_height,
        cap_height=cap_height,
        x_height_ratio=round(x_height / units_per_em, 4),
        cap_height_ratio=round(cap_height / units_per_em, 4),
        ascender_ratio=round(ascender / units_per_em, 4),
        descender_ratio=round(descender / units_per_em, 4),
        stroke_contrast=stroke_contrast,
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_metrics.py path/to/font.ttf")
        sys.exit(1)
    metrics = extract_metrics(sys.argv[1])
    for k, v in asdict(metrics).items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()

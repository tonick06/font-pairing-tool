"""EVOLUTION_LOG cycle 1: fill the monospace category gap.

Downloads monospace families directly from raw.githubusercontent.com,
probing a short list of likely filenames per family instead of listing
the folder via api.github.com (which has a much stricter unauthenticated
rate limit and is what stalled the original download_fonts.py run).
"""

import io
import os
import requests

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# (repo folder, display name, list of candidate filenames to probe in order)
MONOSPACE_FAMILIES = [
    ("ofl/robotomono", "Roboto Mono", ["RobotoMono-Regular.ttf", "static/RobotoMono-Regular.ttf", "RobotoMono[wght].ttf"]),
    ("ofl/sourcecodepro", "Source Code Pro", ["SourceCodePro-Regular.ttf", "static/SourceCodePro-Regular.ttf", "SourceCodePro[wght].ttf"]),
    ("ofl/ibmplexmono", "IBM Plex Mono", ["IBMPlexMono-Regular.ttf", "static/IBMPlexMono-Regular.ttf", "IBMPlexMono[wght].ttf"]),
    ("ofl/jetbrainsmono", "JetBrains Mono", ["JetBrainsMono-Regular.ttf", "static/JetBrainsMono-Regular.ttf", "JetBrainsMono[wght].ttf"]),
    ("ofl/spacemono", "Space Mono", ["SpaceMono-Regular.ttf"]),
    ("ofl/inconsolata", "Inconsolata", ["Inconsolata-Regular.ttf", "static/Inconsolata-Regular.ttf", "Inconsolata[wdth,wght].ttf"]),
    ("ofl/firacode", "Fira Code", ["FiraCode-Regular.ttf", "static/FiraCode-Regular.ttf", "FiraCode[wght].ttf"]),
    ("ofl/courierprime", "Courier Prime", ["CourierPrime-Regular.ttf"]),
    ("ofl/ptmono", "PT Mono", ["PTMono-Regular.ttf"]),
    ("ofl/majormonodisplay", "Major Mono Display", ["MajorMonoDisplay-Regular.ttf"]),
    ("ofl/overpassmono", "Overpass Mono", ["OverpassMono-Regular.ttf", "static/OverpassMono-Regular.ttf", "OverpassMono[wght].ttf"]),
    ("ofl/dmmono", "DM Mono", ["DMMono-Regular.ttf"]),
    ("ofl/robotomono", "Roboto Mono", []),  # placeholder to keep index stable if list edited
]


def _instantiate_if_variable(content: bytes, weight: int = 400) -> bytes:
    ttfont = TTFont(io.BytesIO(content))
    if "fvar" not in ttfont:
        return content
    axes = {a.axisTag: weight if a.axisTag == "wght" else a.defaultValue
            for a in ttfont["fvar"].axes}
    instantiateVariableFont(ttfont, axes, inplace=True)
    buf = io.BytesIO()
    ttfont.save(buf)
    return buf.getvalue()


def download_monospace():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "font-pairing-tool"})

    ok, failed = 0, []
    seen = set()
    for repo_path, display_name, candidates in MONOSPACE_FAMILIES:
        if display_name in seen or not candidates:
            continue
        seen.add(display_name)

        out_path = os.path.join(OUT_DIR, display_name.replace(" ", "") + ".ttf")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            ok += 1
            print(f"SKIP {display_name} (already present)")
            continue

        found = False
        for filename in candidates:
            url = f"{RAW_BASE}/{repo_path}/{filename}"
            try:
                resp = session.get(url, timeout=20)
            except Exception as e:
                continue
            if resp.status_code == 200 and len(resp.content) > 1000:
                content = resp.content
                try:
                    content = _instantiate_if_variable(content)
                except Exception:
                    pass
                with open(out_path, "wb") as f:
                    f.write(content)
                print(f"OK   {display_name} ({filename})")
                ok += 1
                found = True
                break

        if not found:
            failed.append(display_name)
            print(f"FAIL {display_name} -> none of {candidates} resolved")

    print(f"\n{ok} monospace fonts ready, {len(failed)} failed: {failed}")
    return ok, failed


if __name__ == "__main__":
    download_monospace()

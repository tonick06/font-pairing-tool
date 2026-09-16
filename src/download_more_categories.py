"""EVOLUTION_LOG cycle 7: balance the thin slab-serif and display categories.

Same approach as download_monospace.py (cycle 1): probe known static/variable
filenames directly against raw.githubusercontent.com, avoiding the
api.github.com folder-listing rate limit.
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font_download_utils import instantiate_if_variable

RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# (repo folder, display name, category, candidate filenames to probe in order)
NEW_FAMILIES = [
    ("apache/robotoslab", "Roboto Slab", "slab-serif",
     ["RobotoSlab-Regular.ttf", "static/RobotoSlab-Regular.ttf", "RobotoSlab[wght].ttf"]),
    ("ofl/josefinslab", "Josefin Slab", "slab-serif",
     ["JosefinSlab-Regular.ttf", "static/JosefinSlab-Regular.ttf", "JosefinSlab[wght].ttf"]),
    ("ofl/aleo", "Aleo", "slab-serif",
     ["Aleo-Regular.ttf", "static/Aleo-Regular.ttf", "Aleo[wght].ttf"]),
    ("ofl/bevan", "Bevan", "slab-serif", ["Bevan-Regular.ttf"]),
    ("ofl/trocchi", "Trocchi", "slab-serif", ["Trocchi-Regular.ttf"]),
    ("ofl/kreon", "Kreon", "slab-serif",
     ["Kreon-Regular.ttf", "static/Kreon-Regular.ttf", "Kreon[wght].ttf"]),

    ("ofl/comfortaa", "Comfortaa", "display",
     ["Comfortaa-Regular.ttf", "static/Comfortaa-Regular.ttf", "Comfortaa[wght].ttf"]),
    ("ofl/bungee", "Bungee", "display", ["Bungee-Regular.ttf"]),
    ("ofl/baloo2", "Baloo 2", "display",
     ["Baloo2-Regular.ttf", "static/Baloo2-Regular.ttf", "Baloo2[wght].ttf"]),
    ("ofl/bangers", "Bangers", "display", ["Bangers-Regular.ttf"]),
    ("ofl/monoton", "Monoton", "display", ["Monoton-Regular.ttf"]),
    ("ofl/shrikhand", "Shrikhand", "display", ["Shrikhand-Regular.ttf"]),
]


def download_more_categories():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "font-pairing-tool"})

    ok, failed = 0, []
    for repo_path, display_name, category, candidates in NEW_FAMILIES:
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
            except Exception:
                continue
            if resp.status_code == 200 and len(resp.content) > 1000:
                content = resp.content
                try:
                    content = instantiate_if_variable(content)
                except Exception:
                    pass
                with open(out_path, "wb") as f:
                    f.write(content)
                print(f"OK   {display_name} ({filename}) [{category}]")
                ok += 1
                found = True
                break

        if not found:
            failed.append(display_name)
            print(f"FAIL {display_name} -> none of {candidates} resolved")

    print(f"\n{ok} fonts ready, {len(failed)} failed: {failed}")
    return ok, failed


if __name__ == "__main__":
    download_more_categories()

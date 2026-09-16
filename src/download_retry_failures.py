"""EVOLUTION_LOG cycle 18: recover fonts that failed in cycle 9 because
their real filenames use multi-axis variable naming (e.g. [wdth,wght].ttf)
that cycle 9's candidate list only guessed as [wght].ttf. Filenames below
were confirmed directly against the google/fonts repo listing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font_download_utils import instantiate_if_variable

import requests

RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")

# (repo folder, display name, category, confirmed real filename)
RETRY_FAMILIES = [
    ("ofl/notosans", "Noto Sans", "sans-serif", "NotoSans[wdth,wght].ttf"),
    ("ofl/notoserif", "Noto Serif", "serif", "NotoSerif[wdth,wght].ttf"),
    ("ofl/signika", "Signika", "sans-serif", "Signika[GRAD,wght].ttf"),
    ("ofl/saira", "Saira", "sans-serif", "Saira[wdth,wght].ttf"),
    ("ofl/asap", "Asap", "sans-serif", "Asap[wdth,wght].ttf"),
    ("ofl/overpass", "Overpass", "sans-serif", "Overpass[wght].ttf"),
    ("ofl/oldstandardtt", "Old Standard TT", "serif", "OldStandard-Regular.ttf"),
    ("ofl/shadowsintolight", "Shadows Into Light", "display", "ShadowsIntoLight.ttf"),
    ("ofl/fredoka", "Fredoka", "sans-serif", "Fredoka[wdth,wght].ttf"),
    ("ofl/novamono", "Nova Mono", "monospace", "NovaMono.ttf"),
]


def download_retry_failures():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "font-pairing-tool"})

    ok, failed = 0, []
    for repo_path, display_name, category, filename in RETRY_FAMILIES:
        out_path = os.path.join(OUT_DIR, display_name.replace(" ", "") + ".ttf")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            ok += 1
            print(f"SKIP {display_name} (already present)")
            continue

        url = f"{RAW_BASE}/{repo_path}/{filename}"
        try:
            resp = session.get(url, timeout=20)
        except Exception as e:
            failed.append((display_name, str(e)))
            print(f"FAIL {display_name} -> {e}")
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
        else:
            failed.append((display_name, f"HTTP {resp.status_code}"))
            print(f"FAIL {display_name} -> HTTP {resp.status_code} ({filename})")

    print(f"\n{ok} fonts ready, {len(failed)} failed: {failed}")
    return ok, failed


if __name__ == "__main__":
    download_retry_failures()

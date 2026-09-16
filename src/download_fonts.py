"""Milestone 2 (step 1): download a variety of Google Fonts into fonts/.

For each family, lists the family's folder in the google/fonts GitHub repo,
picks a static Regular .ttf if one exists, and otherwise downloads the
variable font and instances it down to a fixed wght=400 static font (this
project treats every font as fixed-weight per the v1 spec).
"""

import io
import os
import time
import requests

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

API_BASE = "https://api.github.com/repos/google/fonts/contents"
RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"

# (repo folder, display family name)
FAMILIES = [
    ("ofl/roboto", "Roboto"), ("ofl/opensans", "Open Sans"), ("ofl/lato", "Lato"),
    ("ofl/montserrat", "Montserrat"), ("ofl/sourcesans3", "Source Sans 3"),
    ("ofl/poppins", "Poppins"), ("ofl/nunito", "Nunito"), ("ofl/raleway", "Raleway"),
    ("ofl/inter", "Inter"), ("ofl/worksans", "Work Sans"), ("ofl/rubik", "Rubik"),
    ("ofl/karla", "Karla"), ("ofl/barlow", "Barlow"), ("ofl/manrope", "Manrope"),
    ("ofl/dmsans", "DM Sans"), ("ofl/ibmplexsans", "IBM Plex Sans"),
    ("ofl/publicsans", "Public Sans"), ("ofl/ptsans", "PT Sans"), ("ofl/cabin", "Cabin"),
    ("ofl/archivo", "Archivo"), ("ofl/figtree", "Figtree"), ("ofl/outfit", "Outfit"),
    ("ofl/spacegrotesk", "Space Grotesk"), ("ofl/urbanist", "Urbanist"),
    ("ofl/sora", "Sora"), ("ofl/lexend", "Lexend"),

    ("ofl/playfairdisplay", "Playfair Display"), ("ofl/merriweather", "Merriweather"),
    ("ofl/lora", "Lora"), ("ofl/ptserif", "PT Serif"),
    ("ofl/sourceserif4", "Source Serif 4"), ("ofl/crimsontext", "Crimson Text"),
    ("ofl/crimsonpro", "Crimson Pro"), ("ofl/ebgaramond", "EB Garamond"),
    ("ofl/librebaskerville", "Libre Baskerville"), ("ofl/cormorant", "Cormorant"),
    ("ofl/cormorantgaramond", "Cormorant Garamond"), ("ofl/bitter", "Bitter"),
    ("ofl/vollkorn", "Vollkorn"), ("ofl/domine", "Domine"), ("ofl/spectral", "Spectral"),
    ("ofl/cardo", "Cardo"), ("ofl/alegreya", "Alegreya"),
    ("ofl/ibmplexserif", "IBM Plex Serif"), ("ofl/literata", "Literata"),
    ("ofl/newsreader", "Newsreader"),

    ("ofl/robotoslab", "Roboto Slab"), ("ofl/josefinslab", "Josefin Slab"),
    ("ofl/zillaslab", "Zilla Slab"), ("ofl/arvo", "Arvo"), ("ofl/rokkitt", "Rokkitt"),
    ("ofl/aleo", "Aleo"),

    ("ofl/oswald", "Oswald"), ("ofl/anton", "Anton"), ("ofl/bebasneue", "Bebas Neue"),
    ("ofl/abrilfatface", "Abril Fatface"), ("ofl/lobster", "Lobster"),
    ("ofl/pacifico", "Pacifico"), ("ofl/righteous", "Righteous"),
    ("ofl/comfortaa", "Comfortaa"), ("ofl/fjallaone", "Fjalla One"),
    ("ofl/alfaslabone", "Alfa Slab One"), ("ofl/passionone", "Passion One"),
    ("ofl/bungee", "Bungee"), ("ofl/staatliches", "Staatliches"),
    ("ofl/baloo2", "Baloo 2"), ("ofl/yesevaone", "Yeseva One"),

    ("ofl/robotomono", "Roboto Mono"), ("ofl/sourcecodepro", "Source Code Pro"),
    ("ofl/ibmplexmono", "IBM Plex Mono"), ("ofl/jetbrainsmono", "JetBrains Mono"),
    ("ofl/spacemono", "Space Mono"), ("ofl/inconsolata", "Inconsolata"),
    ("ofl/firacode", "Fira Code"), ("ofl/courierprime", "Courier Prime"),
    ("ofl/ptmono", "PT Mono"),
]

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")


def _list_folder(repo_path, session, retries=3):
    url = f"{API_BASE}/{repo_path}"
    for attempt in range(retries):
        resp = session.get(url, timeout=20)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 403:
            # rate limited - back off
            time.sleep(3 * (attempt + 1))
            continue
        return None
    return None


def _pick_font_file(entries):
    """Return (filename, is_variable) preferring a static Regular ttf."""
    ttf_files = [e["name"] for e in entries if e["name"].lower().endswith(".ttf")]
    static_dir = [e for e in entries if e["type"] == "dir" and e["name"] == "static"]
    # Prefer an explicit -Regular.ttf at the family root (static family).
    for name in ttf_files:
        if name.lower().endswith("-regular.ttf"):
            return name, False, None
    # Some families keep statics in a static/ subfolder alongside a variable font.
    if static_dir:
        return None, False, "static"
    # Otherwise take the (likely variable) ttf with the shortest name.
    if ttf_files:
        ttf_files.sort(key=len)
        return ttf_files[0], True, None
    return None, False, None


def _instantiate_static(var_font_bytes, weight=400):
    ttfont = TTFont(io.BytesIO(var_font_bytes))
    if "fvar" not in ttfont:
        return ttfont  # not actually variable
    axes = {a.axisTag: weight if a.axisTag == "wght" else a.defaultValue
            for a in ttfont["fvar"].axes}
    instantiateVariableFont(ttfont, axes, inplace=True)
    return ttfont


def download_all():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "font-pairing-tool"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers.update({"Authorization": f"token {token}"})

    ok, failed = 0, []
    for repo_path, display_name in FAMILIES:
        safe_name = display_name.replace(" ", "") + ".ttf"
        out_path = os.path.join(OUT_DIR, safe_name)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            ok += 1
            continue

        entries = _list_folder(repo_path, session)
        if entries is None:
            failed.append((display_name, "folder listing failed"))
            print(f"FAIL {display_name} -> could not list {repo_path}")
            continue

        filename, is_variable_hint, note = _pick_font_file(entries)

        if note == "static":
            static_entries = _list_folder(f"{repo_path}/static", session)
            if static_entries:
                filename2, _, _ = _pick_font_file(static_entries)
                if filename2:
                    raw_url = f"{RAW_BASE}/{repo_path}/static/{filename2}"
                    try:
                        resp = session.get(raw_url, timeout=20)
                        if resp.status_code == 200 and len(resp.content) > 1000:
                            with open(out_path, "wb") as f:
                                f.write(resp.content)
                            ok += 1
                            print(f"OK   {display_name} (static/{filename2})")
                            continue
                    except Exception as e:
                        pass
            filename = None
            # fall through to variable-font pick from root entries
            ttf_files = [e["name"] for e in entries if e["name"].lower().endswith(".ttf")]
            if ttf_files:
                ttf_files.sort(key=len)
                filename = ttf_files[0]

        if not filename:
            failed.append((display_name, "no ttf found"))
            print(f"FAIL {display_name} -> no .ttf in {repo_path}")
            continue

        raw_url = f"{RAW_BASE}/{repo_path}/{filename}"
        try:
            resp = session.get(raw_url, timeout=20)
            if resp.status_code != 200 or len(resp.content) <= 1000:
                failed.append((display_name, f"HTTP {resp.status_code} for {filename}"))
                print(f"FAIL {display_name} -> HTTP {resp.status_code} ({filename})")
                continue

            content = resp.content
            if filename.lower().endswith(".ttf") and ("[" in filename or is_variable_hint):
                try:
                    ttfont = _instantiate_static(content, weight=400)
                    buf = io.BytesIO()
                    ttfont.save(buf)
                    content = buf.getvalue()
                    note_str = " (instanced wght=400)"
                except Exception as e:
                    note_str = f" (used as-is, instancing failed: {e})"
            else:
                note_str = ""

            with open(out_path, "wb") as f:
                f.write(content)
            ok += 1
            print(f"OK   {display_name} ({filename}){note_str}")
        except Exception as e:
            failed.append((display_name, str(e)))
            print(f"FAIL {display_name} -> {e}")

        time.sleep(0.05)

    print(f"\nDownloaded/verified {ok}/{len(FAMILIES)} fonts into {OUT_DIR}")
    if failed:
        print(f"{len(failed)} failures:")
        for name, err in failed:
            print(f"  {name}: {err}")
    return ok, failed


if __name__ == "__main__":
    download_all()

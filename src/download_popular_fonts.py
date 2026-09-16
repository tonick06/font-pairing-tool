"""EVOLUTION_LOG cycle 9: bulk-add a large batch of genuinely popular Google
Fonts the database was still missing, spanning all five categories. Same
raw.githubusercontent.com probing approach as cycles 1 and 7 (no
api.github.com folder listing, so no rate-limit risk).
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font_download_utils import instantiate_if_variable

RAW_BASE = "https://raw.githubusercontent.com/google/fonts/main"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")


def _candidates(stub):
    return [f"{stub}-Regular.ttf", f"static/{stub}-Regular.ttf", f"{stub}[wght].ttf"]


# (repo folder, display name, category, candidate filenames)
NEW_FAMILIES = [
    # sans-serif
    ("ofl/notosans", "Noto Sans", "sans-serif", _candidates("NotoSans")),
    ("ofl/quicksand", "Quicksand", "sans-serif", _candidates("Quicksand")),
    ("ofl/josefinsans", "Josefin Sans", "sans-serif", _candidates("JosefinSans")),
    ("ofl/mulish", "Mulish", "sans-serif", _candidates("Mulish")),
    ("ofl/heebo", "Heebo", "sans-serif", _candidates("Heebo")),
    ("ofl/hind", "Hind", "sans-serif", ["Hind-Regular.ttf"]),
    ("ofl/titilliumweb", "Titillium Web", "sans-serif", ["TitilliumWeb-Regular.ttf"]),
    ("ofl/assistant", "Assistant", "sans-serif", _candidates("Assistant")),
    ("ofl/varelaround", "Varela Round", "sans-serif", ["VarelaRound-Regular.ttf"]),
    ("ofl/firasans", "Fira Sans", "sans-serif", ["FiraSans-Regular.ttf"]),
    ("ofl/signika", "Signika", "sans-serif", _candidates("Signika")),
    ("ofl/catamaran", "Catamaran", "sans-serif", _candidates("Catamaran")),
    ("ofl/exo2", "Exo 2", "sans-serif", _candidates("Exo2")),
    ("ofl/saira", "Saira", "sans-serif", _candidates("Saira")),
    ("ofl/prompt", "Prompt", "sans-serif", ["Prompt-Regular.ttf"]),
    ("ofl/kanit", "Kanit", "sans-serif", ["Kanit-Regular.ttf"]),
    ("ofl/mavenpro", "Maven Pro", "sans-serif", _candidates("MavenPro")),
    ("ofl/rajdhani", "Rajdhani", "sans-serif", ["Rajdhani-Regular.ttf"]),
    ("ofl/chivo", "Chivo", "sans-serif", _candidates("Chivo")),
    ("ofl/asap", "Asap", "sans-serif", _candidates("Asap")),
    ("ofl/overpass", "Overpass", "sans-serif", ["Overpass-Regular.ttf", "static/Overpass-Regular.ttf"]),
    ("ofl/redhatdisplay", "Red Hat Display", "sans-serif", _candidates("RedHatDisplay")),
    ("ofl/redhattext", "Red Hat Text", "sans-serif", _candidates("RedHatText")),
    ("ofl/epilogue", "Epilogue", "sans-serif", _candidates("Epilogue")),
    ("ofl/plusjakartasans", "Plus Jakarta Sans", "sans-serif", _candidates("PlusJakartaSans")),
    ("ofl/bevietnampro", "Be Vietnam Pro", "sans-serif", ["BeVietnamPro-Regular.ttf"]),
    ("ofl/albertsans", "Albert Sans", "sans-serif", _candidates("AlbertSans")),

    # serif
    ("ofl/notoserif", "Noto Serif", "serif", ["NotoSerif-Regular.ttf", "static/NotoSerif-Regular.ttf"]),
    ("ofl/neuton", "Neuton", "serif", ["Neuton-Regular.ttf"]),
    ("ofl/oldstandardtt", "Old Standard TT", "serif", ["OldStandardTT-Regular.ttf"]),
    ("ofl/rasa", "Rasa", "serif", _candidates("Rasa")),
    ("ofl/vidaloka", "Vidaloka", "serif", ["Vidaloka-Regular.ttf"]),
    ("ofl/marcellus", "Marcellus", "serif", ["Marcellus-Regular.ttf"]),
    ("ofl/prata", "Prata", "serif", ["Prata-Regular.ttf"]),
    ("ofl/cinzel", "Cinzel", "serif", _candidates("Cinzel")),
    ("ofl/petrona", "Petrona", "serif", _candidates("Petrona")),
    ("ofl/faustina", "Faustina", "serif", _candidates("Faustina")),
    ("ofl/sortsmillgoudy", "Sorts Mill Goudy", "serif", ["SortsMillGoudy-Regular.ttf"]),

    # slab-serif
    ("ofl/podkova", "Podkova", "slab-serif", _candidates("Podkova")),
    ("ofl/sanchez", "Sanchez", "slab-serif", ["Sanchez-Regular.ttf"]),
    ("ofl/trirong", "Trirong", "slab-serif", ["Trirong-Regular.ttf"]),
    ("ofl/rosarivo", "Rosarivo", "slab-serif", ["Rosarivo-Regular.ttf"]),
    ("ofl/breeserif", "Bree Serif", "slab-serif", ["BreeSerif-Regular.ttf"]),

    # display
    ("ofl/specialelite", "Special Elite", "display", ["SpecialElite-Regular.ttf"]),
    ("ofl/permanentmarker", "Permanent Marker", "display", ["PermanentMarker-Regular.ttf"]),
    ("ofl/caveat", "Caveat", "display", _candidates("Caveat")),
    ("ofl/satisfy", "Satisfy", "display", ["Satisfy-Regular.ttf"]),
    ("ofl/kalam", "Kalam", "display", ["Kalam-Regular.ttf"]),
    ("ofl/indieflower", "Indie Flower", "display", ["IndieFlower-Regular.ttf"]),
    ("ofl/amaticsc", "Amatic SC", "display", ["AmaticSC-Regular.ttf"]),
    ("ofl/sacramento", "Sacramento", "display", ["Sacramento-Regular.ttf"]),
    ("ofl/dancingscript", "Dancing Script", "display", _candidates("DancingScript")),
    ("ofl/greatvibes", "Great Vibes", "display", ["GreatVibes-Regular.ttf"]),
    ("ofl/shadowsintolight", "Shadows Into Light", "display", ["ShadowsIntoLight-Regular.ttf"]),
    ("ofl/patrickhand", "Patrick Hand", "display", ["PatrickHand-Regular.ttf"]),
    ("ofl/architectsdaughter", "Architects Daughter", "display", ["ArchitectsDaughter-Regular.ttf"]),
    ("ofl/gochihand", "Gochi Hand", "display", ["GochiHand-Regular.ttf"]),
    ("ofl/lobstertwo", "Lobster Two", "display", ["LobsterTwo-Regular.ttf"]),
    ("ofl/bowlbyone", "Bowlby One", "display", ["BowlbyOne-Regular.ttf"]),
    ("ofl/chewy", "Chewy", "display", ["Chewy-Regular.ttf"]),
    ("ofl/luckiestguy", "Luckiest Guy", "display", ["LuckiestGuy-Regular.ttf"]),
    ("ofl/titanone", "Titan One", "display", ["TitanOne-Regular.ttf"]),
    ("ofl/sniglet", "Sniglet", "display", ["Sniglet-Regular.ttf"]),
    ("ofl/fredoka", "Fredoka", "display", _candidates("Fredoka")),
    ("ofl/concertone", "Concert One", "display", ["ConcertOne-Regular.ttf"]),

    # monospace
    ("ofl/cousine", "Cousine", "monospace", ["Cousine-Regular.ttf"]),
    ("ofl/ubuntumono", "Ubuntu Mono", "monospace", ["UbuntuMono-Regular.ttf"]),
    ("ofl/anonymouspro", "Anonymous Pro", "monospace", ["AnonymousPro-Regular.ttf"]),
    ("ofl/vt323", "VT323", "monospace", ["VT323-Regular.ttf"]),
    ("ofl/sharetechmono", "Share Tech Mono", "monospace", ["ShareTechMono-Regular.ttf"]),
    ("ofl/novamono", "Nova Mono", "monospace", ["NovaMono-Regular.ttf"]),
    ("ofl/cutivemono", "Cutive Mono", "monospace", ["CutiveMono-Regular.ttf"]),
    ("ofl/b612mono", "B612 Mono", "monospace", ["B612Mono-Regular.ttf"]),
]


def download_popular_fonts():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "font-pairing-tool"})

    ok, failed = 0, []
    for repo_path, display_name, category, candidates in NEW_FAMILIES:
        out_path = os.path.join(OUT_DIR, display_name.replace(" ", "") + ".ttf")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            ok += 1
            continue

        found = False
        for filename in candidates:
            url = f"{RAW_BASE}/{repo_path}/{filename}"
            try:
                resp = session.get(url, timeout=15)
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
    download_popular_fonts()

"""Shared helper for the download_*.py scripts (cycles 1, 7, 9): instance a
variable font down to a single static weight, since the rest of the tool
treats every font as fixed-weight (see README's Non-goals).
"""

import io

from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont


def instantiate_if_variable(content: bytes, weight: int = 400) -> bytes:
    """Return content unchanged if it's not a variable font; otherwise
    instance it at the given weight (other axes pinned to their defaults)
    and return the resulting static font's bytes."""
    ttfont = TTFont(io.BytesIO(content))
    if "fvar" not in ttfont:
        return content
    axes = {a.axisTag: weight if a.axisTag == "wght" else a.defaultValue
            for a in ttfont["fvar"].axes}
    instantiateVariableFont(ttfont, axes, inplace=True)
    buf = io.BytesIO()
    ttfont.save(buf)
    return buf.getvalue()

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from generate_gallery import generate_gallery


def test_gallery_generates_self_contained_html():
    with tempfile.TemporaryDirectory() as tmp:
        out_path = os.path.join(tmp, "gallery.html")
        result_path = generate_gallery(
            showcase_fonts=[("Playfair Display", "serif")], top_n=1, out_path=out_path
        )
        assert result_path == out_path
        assert os.path.exists(out_path)
        with open(out_path, encoding="utf-8") as f:
            content = f.read()
        assert "Playfair Display" in content
        assert "data:image/png;base64," in content

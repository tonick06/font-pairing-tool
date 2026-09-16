import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI = os.path.join(ROOT, "fontpair.py")


def _run(*args):
    return subprocess.run(
        [sys.executable, CLI, *args], capture_output=True, text=True, cwd=ROOT
    )


def test_list_runs_and_lists_fonts():
    result = _run("list")
    assert result.returncode == 0
    assert "fonts." in result.stdout


def test_list_filters_by_category():
    result = _run("list", "--category", "monospace")
    assert result.returncode == 0
    assert "monospace" in result.stdout
    assert "serif" not in result.stdout.replace("monospace", "")


def test_recommend_known_font():
    result = _run("recommend", "Playfair Display", "--top", "3")
    assert result.returncode == 0
    assert "Top 3 pairings for Playfair Display" in result.stdout


def test_recommend_unknown_font_errors_cleanly():
    result = _run("recommend", "Definitely Not A Real Font")
    assert result.returncode != 0
    assert "Error" in result.stderr


def test_score_known_pair():
    result = _run("score", "Playfair Display", "Source Sans 3")
    assert result.returncode == 0
    assert "Playfair Display + Source Sans 3" in result.stdout

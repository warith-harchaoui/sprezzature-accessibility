"""Tests for sprezzature-accessibility."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

import pytest


def test_import() -> None:
    """The package imports without error."""
    import sprezzature_accessibility  # noqa: F401


def test_lint_a11y_help() -> None:
    """lint_a11y --help exits 0."""
    result = subprocess.run(
        [sys.executable, "scripts/lint_a11y.py", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent,
    )
    assert result.returncode == 0
    assert "lint" in result.stdout.lower() or "a11y" in result.stdout.lower()


def test_lint_a11y_clean_html() -> None:
    """A well-formed HTML file produces 0 findings."""
    html = textwrap.dedent("""\
        <!DOCTYPE html>
        <html lang="en">
        <head><meta charset="utf-8"><title>Test</title></head>
        <body>
          <img src="chart.png" alt="Monthly revenue bar chart">
          <a href="/about">About us</a>
          <button aria-label="Close dialog">X</button>
          <label for="email">Email</label>
          <input id="email" type="email">
          <h1>Title</h1>
          <h2>Section</h2>
        </body>
        </html>
    """)
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        result = subprocess.run(
            [sys.executable, "scripts/lint_a11y.py", str(tmp)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 0, result.stdout
    finally:
        tmp.unlink(missing_ok=True)


def test_lint_a11y_catches_missing_alt() -> None:
    """An img without alt attribute produces a finding and exit code 1."""
    html = textwrap.dedent("""\
        <!DOCTYPE html>
        <html lang="en">
        <body>
          <img src="photo.jpg">
        </body>
        </html>
    """)
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        result = subprocess.run(
            [sys.executable, "scripts/lint_a11y.py", str(tmp)],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 1
        assert "img-missing-alt" in result.stdout
    finally:
        tmp.unlink(missing_ok=True)

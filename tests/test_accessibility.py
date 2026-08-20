"""Tests for sprezzature-accessibility."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

# scripts/ uses sys.path insertions at import time (see lint_a11y.py); mirror
# that here so the direct-import tests below can reach lint_a11y and its
# lint_file/fix_file entry points without going through a subprocess.
SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))


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


def _findings_for(html: str) -> list:
    """Write ``html`` to a temp file and return lint_a11y's findings for it.

    Goes through the real :func:`lint_file` entry point (not a reimplemented
    rule loop) so these tests exercise the same code path the CLI uses.
    """
    from lint_a11y import lint_file

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        return lint_file(tmp, ignored=set())
    finally:
        tmp.unlink(missing_ok=True)


def test_check_button_empty() -> None:
    """A <button> with no text and no aria-label triggers button-empty."""
    findings = _findings_for('<button></button>')
    assert any(f.rule == "button-empty" for f in findings)


def test_check_button_with_icon_is_clean() -> None:
    """A <button> whose only content is an <svg> is not flagged."""
    findings = _findings_for('<button><svg></svg></button>')
    assert not any(f.rule == "button-empty" for f in findings)


def test_check_heading_skip() -> None:
    """<h2> directly followed by <h4> is a downward skip."""
    findings = _findings_for("<h1>Title</h1><h2>Section</h2><h4>Sub-sub</h4>")
    assert any(f.rule == "heading-skip" for f in findings)


def test_check_color_only_state() -> None:
    """A red/green Tailwind token with no text or icon is color-only-state."""
    findings = _findings_for('<span class="text-red-500"></span>')
    assert any(f.rule == "color-only-state" for f in findings)


def test_check_color_only_state_with_label_is_clean() -> None:
    """The same token with a text label is not flagged."""
    findings = _findings_for('<span class="text-red-500">Failed</span>')
    assert not any(f.rule == "color-only-state" for f in findings)


def test_check_motion_reduce_guard() -> None:
    """animate-spin without a motion-reduce: peer triggers the guard rule."""
    findings = _findings_for('<div class="animate-spin"></div>')
    assert any(f.rule == "motion-no-reduce-guard" for f in findings)


def test_fix_tabindex_positive() -> None:
    """--fix demotes a positive tabindex to 0, in place, idempotently."""
    from lint_a11y import fix_file

    html = '<html lang="en"><body><div tabindex="3"></div></body></html>\n'
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        applied, skipped, remaining = fix_file(tmp, ignored=set())
        assert applied >= 1
        fixed = tmp.read_text(encoding="utf-8")
        assert 'tabindex="0"' in fixed
        assert 'tabindex="3"' not in fixed
        # Re-running against the now-fixed file must be a no-op.
        applied_again, _, _ = fix_file(tmp, ignored=set())
        assert applied_again == 0
    finally:
        tmp.unlink(missing_ok=True)


def test_fix_motion_reduce_guard() -> None:
    """--fix appends a motion-reduce: peer to an animated element's classes."""
    from lint_a11y import fix_file

    html = '<html lang="en"><body><div class="animate-spin"></div></body></html>\n'
    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
        f.write(html)
        tmp = Path(f.name)
    try:
        applied, _, _ = fix_file(tmp, ignored=set())
        assert applied >= 1
        fixed = tmp.read_text(encoding="utf-8")
        assert "motion-reduce:" in fixed
    finally:
        tmp.unlink(missing_ok=True)

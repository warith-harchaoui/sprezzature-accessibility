"""
The tracking rule, and the line between running text and display type.

Narrowing a linter's exemption is the easy way to make it quiet, so both
halves are here: a dashboard figure is exempt, and ordinary prose is not.

The reason this file exists is worth keeping. `sprezzature-ui` — the package
whose job is to set the example — shipped a card component that failed this
very lint, for a KPI number set at `text-4xl tracking-tight`. The rule's own
docstring had already promised that display type was exempt; it simply could
not recognise display type inside a `<p>`.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

from sprezzature_accessibility import lint_file

# ── Display type is not running text ───────────────────────────────────────


def test_tracking_tight_on_a_dashboard_figure_is_not_flagged(tmp_path):
    """A 4xl number in a tile is one glance, not a paragraph.

    The evidence behind this rule is about *continuous reading*: narrower
    letter-spacing slows dyslexic readers through prose. It does not reach a
    KPI figure, and tightening one is ordinary typography.

    Found the hard way — `sprezzature-ui`, the package whose job is to set the
    example, shipped a card that failed this lint for exactly that. The
    docstring had promised the exemption for headings; it could not see it
    inside a `<p>`.
    """
    page = tmp_path / "tile.html"
    page.write_text(
        '<html lang="en"><body>'
        '<p class="mt-1 text-4xl font-bold tracking-tight tabular-nums">12,438</p>'
        "</body></html>"
    )
    rules = {f.rule for f in lint_file(page, frozenset())}
    assert "body-text-tracking-tight" not in rules


def test_tracking_tight_on_running_text_is_still_flagged(tmp_path):
    """The rule must still do the thing it exists for.

    Narrowing an exemption is the easy way to make a linter quiet, so this is
    the other half of the pair: ordinary prose at ordinary size still fails.
    """
    page = tmp_path / "prose.html"
    page.write_text(
        '<html lang="en"><body>'
        '<p class="tracking-tight">Several sentences of ordinary running text, '
        "set at an ordinary size, which is exactly what this rule protects.</p>"
        "</body></html>"
    )
    rules = {f.rule for f in lint_file(page, frozenset())}
    assert "body-text-tracking-tight" in rules


def test_an_arbitrary_pixel_size_earns_the_same_exemption(tmp_path):
    """A design system that pins exact sizes should not lose the exemption."""
    page = tmp_path / "pinned.html"
    page.write_text(
        '<html lang="en"><body>'
        '<p class="text-[34px] tracking-tight">12,438</p>'
        '<p class="text-[13px] tracking-tight">a caption, small and tight</p>'
        "</body></html>"
    )
    findings = [f for f in lint_file(page, frozenset()) if f.rule == "body-text-tracking-tight"]
    assert len(findings) == 1, "the big figure is exempt, the small caption is not"


def test_linting_a_file_needs_nothing_but_the_file(tmp_path):
    """`lint_file(path)` suppresses nothing, like the CLI with no --ignore.

    It had no default while `lint_html`, the function it wraps, did. So the
    file entry point -- the one a caller reaches for first, and the one the
    sibling repository's site guard tried to call -- was strictly harder to
    call than the string entry point behind it, and demanded an opinion about
    rule suppression from a caller who has none.
    """
    page = tmp_path / "bare.html"
    page.write_text('<html><body><img src="a.png"></body></html>', encoding="utf-8")

    rules = {f.rule for f in lint_file(page)}
    assert {"img-missing-alt", "html-missing-lang"} <= rules, sorted(rules)

    quiet = {f.rule for f in lint_file(page, {"img-missing-alt"})}
    assert "img-missing-alt" not in quiet, (
        "passing ignored= to lint_file no longer suppresses"
    )
    assert "html-missing-lang" in quiet, "it suppressed more than it was asked to"

"""
The seven reading rules: dyslexia and other reading difficulties.

Each rule gets the pair this suite insists on: the markup it exists to catch,
and the nearest markup it must leave alone. A reading rule that fires on a
short label, a link or a centred hero line would be switched off within a
week, and then it protects nobody.

Sources behind the rules: WCAG 2.2 success criterion 1.4.8 Visual
Presentation (AAA), the British Dyslexia Association's Dyslexia Style Guide,
and Rello & Baeza-Yates (2013) on italic type. See
``references/lint-rules.md``.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import pytest
from sprezzature_accessibility_scripts.lint_a11y import (
    CENTERED_LONG_WORDS,
    LONG_PASSAGE_WORDS,
    lint_html,
)

#: Twenty ordinary words, enough to be a passage for every rule but centring.
PROSE = (
    "Reading a long paragraph is a different task from reading a short label, "
    "and the evidence behind these rules is about that task alone."
)
#: Forty words, enough for the centring rule as well.
LONG_PROSE = PROSE + " " + PROSE
SHORT = "Read the guide"


def _rules(body: str) -> list[str]:
    """Rule ids found in a full page wrapping ``body``."""
    page = f'<html lang="en"><body>{body}</body></html>'
    return [f.rule for f in lint_html(page)]


def test_the_fixture_lengths_match_the_thresholds() -> None:
    """The texts above sit on the right side of each threshold."""
    assert len(PROSE.split()) >= LONG_PASSAGE_WORDS
    assert len(PROSE.split()) < CENTERED_LONG_WORDS
    assert len(LONG_PROSE.split()) >= CENTERED_LONG_WORDS
    assert len(SHORT.split()) < LONG_PASSAGE_WORDS


# ── body-text-justified ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        f'<p class="text-justify">{PROSE}</p>',
        f'<div class="md:text-justify"><p>{PROSE}</p></div>',
        f'<p style="text-align: justify">{PROSE}</p>',
        f'<p align="justify">{PROSE}</p>',
        f"<style>article p {{ text-align: justify; }}</style><article><p>{PROSE}</p></article>",
    ],
    ids=["class", "inherited-at-md", "inline-style", "align-attr", "style-block"],
)
def test_justified_running_text_is_flagged(body: str) -> None:
    """Justification reaches running text by every route a page can take."""
    assert "body-text-justified" in _rules(body)


@pytest.mark.parametrize(
    "body",
    [
        f'<p class="text-left">{PROSE}</p>',
        f'<p class="text-justify">{SHORT}</p>',
        f'<div class="text-justify"><p class="text-left">{PROSE}</p></div>',
        f'<style>[data-x] p {{ text-align: justify; }}</style><p>{PROSE}</p>',
        f'<p class="hover:text-justify">{PROSE}</p>',
    ],
    ids=["left", "short-label", "overridden", "conditional-selector", "state-variant"],
)
def test_text_that_is_not_justified_passes(body: str) -> None:
    """Left text, a short label, an override and a conditional rule are clean."""
    assert "body-text-justified" not in _rules(body)


# ── body-text-centered-long ────────────────────────────────────────────────


def test_a_long_centred_paragraph_is_flagged() -> None:
    """Forty centred words: every line starts somewhere else."""
    assert "body-text-centered-long" in _rules(f'<p class="text-center">{LONG_PROSE}</p>')


def test_a_centred_lead_under_a_hero_heading_passes() -> None:
    """Twenty centred words is the settled hero-lead convention, not a passage."""
    rules = _rules(f'<section class="text-center"><h1>Title</h1><p>{PROSE}</p></section>')
    assert "body-text-centered-long" not in rules


# ── body-text-italic-long ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        f'<p class="italic">{PROSE}</p>',
        f"<p><em>{PROSE}</em></p>",
        f'<blockquote style="font-style: italic"><p>{PROSE}</p></blockquote>',
    ],
    ids=["class", "em", "inherited-style"],
)
def test_a_long_italic_passage_is_flagged(body: str) -> None:
    """Twenty words in italic, from a class, a tag or an inherited style."""
    assert _rules(body).count("body-text-italic-long") == 1, "reported once, not per element"


@pytest.mark.parametrize(
    "body",
    [
        f"<p>{PROSE} <em>only these words</em></p>",
        f'<p class="italic">{SHORT}</p>',
        f'<p class="italic">Some <span class="not-italic">{PROSE}</span></p>',
    ],
    ids=["emphasis", "short", "turned-off"],
)
def test_emphasis_of_a_few_words_passes(body: str) -> None:
    """Italic emphasis on a few words is what italic is for."""
    assert "body-text-italic-long" not in _rules(body)


# ── body-text-all-caps-long ────────────────────────────────────────────────


def test_a_long_uppercase_passage_is_flagged() -> None:
    """A transform to capitals over a paragraph."""
    assert "body-text-all-caps-long" in _rules(f'<p class="uppercase">{PROSE}</p>')


def test_text_typed_in_capitals_is_flagged() -> None:
    """Capitals typed in the source, with no transform at all."""
    assert "body-text-all-caps-long" in _rules(f"<p>{PROSE.upper()}</p>")


@pytest.mark.parametrize(
    "body",
    [
        '<p class="text-xs uppercase tracking-wide">New this week</p>',
        f"<p>The WCAG, the BDA and the W3C agree on this. {PROSE}</p>",
    ],
    ids=["eyebrow-label", "acronyms-in-prose"],
)
def test_short_capitals_and_acronyms_pass(body: str) -> None:
    """An eyebrow label and a few acronyms in prose are not a passage in capitals."""
    assert "body-text-all-caps-long" not in _rules(body)


# ── body-text-leading-tight ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        f'<p class="leading-tight">{PROSE}</p>',
        f'<div class="leading-none"><p>{PROSE}</p></div>',
        f'<p class="text-sm">{PROSE}</p>',
        f'<p style="line-height: 1.2">{PROSE}</p>',
        f'<p class="leading-[1.3]">{PROSE}</p>',
        f'<p class="leading-relaxed md:text-xl">{PROSE}</p>',
    ],
    ids=["tight", "inherited", "text-sm-default", "inline", "arbitrary", "size-overrides-at-md"],
)
def test_crowded_lines_are_flagged(body: str) -> None:
    """Line height under 1.5, however it got there."""
    assert "body-text-leading-tight" in _rules(body)


@pytest.mark.parametrize(
    "body",
    [
        f'<p class="leading-relaxed">{PROSE}</p>',
        f'<p class="text-sm leading-6">{PROSE}</p>',
        f'<p class="text-sm/6">{PROSE}</p>',
        f"<p>{PROSE}</p>",
        f'<p class="leading-tight">{SHORT}</p>',
        f'<p class="text-4xl leading-none">{PROSE}</p>',
        f'<h2 class="leading-tight">{PROSE}</h2>',
    ],
    ids=["relaxed", "sm-with-leading", "slash-shorthand", "unset", "short", "display", "heading"],
)
def test_comfortable_or_exempt_lines_pass(body: str) -> None:
    """Enough leading, a short label, display type and headings are clean."""
    assert "body-text-leading-tight" not in _rules(body)


# ── body-text-line-too-long ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        f'<div class="max-w-4xl"><p>{LONG_PROSE}</p></div>',
        f'<p class="max-w-[100ch]">{LONG_PROSE}</p>',
        f"<p>{LONG_PROSE}</p>",
    ],
    ids=["max-w-4xl", "arbitrary-ch", "unbounded-page"],
)
def test_long_lines_are_flagged(body: str) -> None:
    """Over 80 characters at some screen width."""
    assert "body-text-line-too-long" in _rules(body)


@pytest.mark.parametrize(
    "body",
    [
        f'<div class="max-w-prose"><p>{LONG_PROSE}</p></div>',
        f'<div class="max-w-6xl"><div class="grid sm:grid-cols-3"><p>{LONG_PROSE}</p></div></div>',
        f'<div class="max-w-6xl"><div class="flex"><img alt="" src="a.png"><p>{LONG_PROSE}</p></div></div>',
        f'<div class="max-w-6xl"><p>{SHORT}</p></div>',
        '<link rel="stylesheet" href="site.css">' + f"<p>{LONG_PROSE}</p>",
        f'<div class="max-w-2xl"><p class="text-lg">{LONG_PROSE}</p></div>',
    ],
    ids=["prose", "three-columns", "flex-row", "short", "linked-stylesheet", "2xl-at-lg-size"],
)
def test_bounded_or_undecidable_lines_pass(body: str) -> None:
    """A prose measure, a grid cell, a flex row, one short line, a hidden stylesheet."""
    assert "body-text-line-too-long" not in _rules(body)


# ── text-underline-not-link ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "body",
    [
        '<p>Read <span class="underline">this part</span> twice.</p>',
        "<p>Read <u>this part</u> twice.</p>",
        '<p>Read <strong style="text-decoration: underline">this</strong>.</p>',
    ],
    ids=["class", "u-tag", "inline-style"],
)
def test_underlined_plain_text_is_flagged(body: str) -> None:
    """An underline that promises a link and leads nowhere."""
    assert "text-underline-not-link" in _rules(body)


@pytest.mark.parametrize(
    "body",
    [
        '<p>Read <a class="underline" href="/guide">the guide</a>.</p>',
        '<a href="/g"><span class="underline">the guide</span></a>',
        '<p><span class="hover:underline">hover only</span></p>',
        '<p><abbr class="underline decoration-dotted" title="Web Content">WCAG</abbr></p>',
        '<button class="underline" type="button">More</button>',
    ],
    ids=["link", "inside-link", "hover-only", "abbr", "button"],
)
def test_links_and_controls_keep_their_underline(body: str) -> None:
    """Links, text inside links, hover states, abbreviations and buttons pass."""
    assert "text-underline-not-link" not in _rules(body)


def test_a_hidden_passage_is_not_read() -> None:
    """Text nobody sees on screen is not judged for how it reads on screen."""
    body = f'<div hidden><p class="text-justify italic uppercase">{LONG_PROSE}</p></div>'
    reading = {r for r in _rules(body) if r.startswith(("body-text-", "text-underline"))}
    assert not reading, reading


# ── The make side: the reading preset ──────────────────────────────────────


def test_the_preset_keeps_its_first_block_byte_for_byte() -> None:
    """``--spacing-only`` is what 1.5 printed, so a pasted copy stays valid."""
    from sprezzature_accessibility_scripts.text_spacing_preset import build_css, build_preset

    assert build_preset(spacing_only=True) == build_css()
    assert build_preset().startswith(build_css())


def test_the_reading_block_answers_the_reading_rules() -> None:
    """Measure, start alignment, upright type, own case: one line per rule."""
    from sprezzature_accessibility_scripts.text_spacing_preset import build_preset

    css = build_preset()
    for declaration in (
        "max-width: 70ch;",
        "text-align: start;",
        "font-style: normal;",
        "text-transform: none;",
        "line-height: 1.5;",
    ):
        assert declaration in css, declaration
    assert '[data-text-spacing="comfortable"] td {\n  max-width' not in css
    assert "font-family" not in css, "no dyslexia font: the evidence does not support one"


def test_a_zero_measure_leaves_the_width_alone() -> None:
    """``--measure 0`` drops the max-width and keeps the rest."""
    from sprezzature_accessibility_scripts.text_spacing_preset import build_preset

    css = build_preset(measure_ch=0)
    assert "max-width" not in css
    assert "text-align: start;" in css


@pytest.mark.parametrize("flags", [[], ["--spacing-only"], ["--measure", "65"]])
def test_the_command_runs_under_its_new_name(flags: list[str], capsys) -> None:
    """The reading command prints CSS for each flag it documents."""
    from sprezzature_accessibility_scripts.text_spacing_preset import main

    assert main(flags) == 0
    out = capsys.readouterr().out
    assert "letter-spacing: 0.12em;" in out
    assert ("max-width" in out) is (flags != ["--spacing-only"])
    if flags[:1] == ["--measure"]:
        assert "max-width: 65ch;" in out

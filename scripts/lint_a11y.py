#!/usr/bin/env python3
"""
lint_a11y
=========

Accessibility linter for HTML emitted by (or for) the ``sprezzature``
skill. "Accessible" here means concretely: can someone using a screen
reader, a keyboard alone (no mouse), or a browser's reduced-motion
setting still use the page, and can someone with dyslexia read it
without losing their line? The twenty-seven rules below each check for
one source-level defect that breaks that experience, for example an
``<img>`` with no ``alt`` text, which is as invisible to a screen
reader as if the image were missing from the page entirely.

The linter is **static**: it never opens a browser, never builds a DOM
(the tree of elements a browser assembles while rendering a page,
which is what a screen reader actually reads from), never runs
JavaScript. It only reads the HTML text, so it drops straight into a
code-emit pipeline or a pre-commit hook with no Chromium to install.

The twenty-seven rules cover the violations that account for the bulk of
real-world WCAG (Web Content Accessibility Guidelines, the W3C
standard that defines what "accessible" means for the web) and
WAI-ARIA (Web Accessibility Initiative, Accessible Rich Internet
Applications, the attribute vocabulary like ``role`` and
``aria-label`` that lets custom widgets describe themselves to a
screen reader) failures. Every one of them is decidable from the HTML
source alone; none needs the runtime DOM.

Rule catalogue
--------------
========================  =====================================================
``img-missing-alt``         ``<img>`` with no ``alt`` attribute. Empty
                            ``alt=""`` is correct for decorative images;
                            *omitting* the attribute is not.
``img-redundant-aria``      ``alt=""`` plus ``role="presentation"`` or
                            ``aria-hidden="true"``: redundant.
``a-missing-href``          ``<a>`` without ``href`` (use ``<button>``).
``a-empty``                 ``<a>`` with no text and no accessible name.
``button-empty``            ``<button>`` with no text, no ``aria-label`` or
                            ``aria-labelledby``, and no ``<svg>`` / ``<img>``.
``div-onclick``             ``<div>`` / ``<span>`` with ``onclick`` but no
                            ``role="button"`` and ``tabindex``.
``input-missing-label``     ``<input>`` not wrapped in a ``<label>``, not
                            referenced by a ``<label for=>``, and with neither
                            ``aria-label`` nor ``aria-labelledby``.
``dialog-missing-close``    ``<dialog>`` without a close affordance
                            (``<button>``, ``value="cancel"``, ``[autofocus]``).
``html-missing-lang``       ``<html>`` without ``lang``.
``tabindex-positive``       ``tabindex`` ≥ 1.
``aria-hidden-interactive`` ``aria-hidden="true"`` on a button / link / input that
                            is **still focusable**. Paired with ``tabindex="-1"``,
                            ``disabled`` or ``inert`` it is the correct way to hide
                            a duplicate control, and is not flagged.
``heading-skip``            Headings out of order (e.g. ``<h2>`` → ``<h4>``).
``color-only-state``        Tailwind ``*-red-*`` / ``*-green-*`` on a span
                            with no icon, label, or text sibling. Catches the
                            "red is bad / green is good" anti-pattern.
``motion-no-reduce-guard``  ``animate-{spin,ping,pulse,bounce}``,
                            ``transition-transform`` or ``transition-all``
                            without a ``motion-reduce:`` peer.
``body-text-tracking-tight`` Tailwind ``tracking-tight`` / ``tracking-tighter``
                            (negative letter-spacing) on a body-text element
                            (``p``, ``li``, ``dd``, ``blockquote``, ``td``,
                            ``figcaption``). Reduced letter-spacing is exactly
                            the anti-pattern a 2012 Zorzi et al. study found
                            slows reading for dyslexic readers; the same
                            tokens on a heading or nav label are unflagged.
``video-missing-captions``  ``<video>`` with no ``<track kind="captions">`` or
                            ``kind="subtitles"`` (WCAG 1.2.2). A ``muted``
                            video without ``controls`` is decorative, exempt.
``audio-missing-transcript`` ``<audio>`` with no track and no accessible name
                            pointing at a transcript (WCAG 1.2.1).
``track-missing-srclang``   ``<track>`` without ``srclang``.
``media-missing-controls``  ``<video>`` / ``<audio>`` without ``controls``
                            (WCAG 2.1.1). Decorative video exempt.
``media-autoplay-sound``    ``autoplay`` without ``muted`` (WCAG 1.4.2).
``body-text-justified``     Justified running text (WCAG 1.4.8, F88; BDA).
``body-text-centered-long`` A centred paragraph of 30 words or more (BDA).
``body-text-italic-long``   15 words or more in italic (BDA; Rello &
                            Baeza-Yates 2013).
``body-text-all-caps-long`` 15 words or more in capitals, transformed or typed.
``body-text-leading-tight`` Line height under 1.5 on running text (WCAG 1.4.8).
``body-text-line-too-long`` Lines over 80 characters (WCAG 1.4.8).
``text-underline-not-link`` Underlined text that is not a link (BDA).
========================  =====================================================

Output
------
Plain-text report by default; use ``--format json`` for machine consumption.
Exit code ``1`` on any finding (unless ``--ignore`` covers it), ``2`` on a
usage error such as a path that does not exist, ``0`` otherwise. The script can be pointed at a single file or a directory.

Usage
-----
::

    # Lint a single page
    python lint_a11y.py public/index.html

    # Lint a tree
    python lint_a11y.py public/

    # JSON output for CI
    python lint_a11y.py --format json public/index.html

    # Suppress two rules
    python lint_a11y.py --ignore heading-skip,motion-no-reduce-guard public/

Notes
-----
* Python 3.10+, the standard library plus click (``html.parser``, ``pathlib``,
  and click for the command line).
* The parser is forgiving: it walks documents that contain mixed-case
  tags, missing closures, and inline scripts without raising.
* This linter is a *first pass*, not a replacement for ``axe-core`` or
  manual screen-reader testing. It catches the violations easiest to fix.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path as _PathHelper

# Shared click helpers: prog name, -h/--help, -V/--version, argparse exit codes.
sys.path.insert(0, str(_PathHelper(__file__).resolve().parent))
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from _lang import detect_text_language, extract_body_text  # noqa: E402

# ── Data structures ────────────────────────────────────────────────────────

@dataclass
class Element:
    """
    Minimal representation of one HTML element captured during parsing.

    Attributes
    ----------
    tag : str
        Lower-cased tag name (``"img"``, ``"button"``, …).
    attrs : dict
        Attribute map. Boolean attributes resolve to the empty string.
    line : int
        1-based source line of the element's opening tag.
    text : str
        Concatenated text content of the element (children stripped).
    children : list of Element
        Direct element children, in source order.
    parent : Element or None
        Parent element, or ``None`` for the synthetic root.
    """

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    line: int = 0
    text: str = ""
    children: list[Element] = field(default_factory=list)
    parent: Element | None = None


@dataclass
class Finding:
    """
    One reported accessibility violation.

    Attributes
    ----------
    rule : str
        Rule identifier (e.g. ``"img-missing-alt"``).
    line : int
        1-based source line of the offending element.
    message : str
        Human-readable explanation suitable for a console line.
    """

    rule: str
    line: int
    message: str


# ── HTML walker ────────────────────────────────────────────────────────────

# Void elements that never have a closing tag in HTML5; ``html.parser`` does
# not flag them, so the walker maintains an explicit list.
VOID_ELEMENTS: frozenset[str] = frozenset({
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "keygen", "link", "meta", "param", "source", "track", "wbr",
})


class TreeBuilder(HTMLParser):
    """
    Build a lightweight element tree from an HTML string.

    The parser is intentionally forgiving — case-folding tag names, treating
    void elements as self-closing, and collecting source line numbers so
    findings can be reported usefully.
    """

    def __init__(self) -> None:
        # ``convert_charrefs=True`` so a character reference is text. With
        # False, html.parser hands ``&times;`` to ``handle_entityref``, which
        # nothing here implements, and the character was lost: a close button
        # whose whole label is ``&times;`` was reported as having no name.
        """Initialise the audit parser's element and text accumulators."""
        super().__init__(convert_charrefs=True)
        # The root is a synthetic ``html`` element so the tree always has a
        # single entry point; the real ``<html>`` becomes its only child.
        self.root: Element = Element(tag="root", line=0)
        self.stack: list[Element] = [self.root]

    # html.parser hooks --------------------------------------------------

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # ``getpos()`` returns (line, column) for the current token; only
        # the line is preserved.
        """Record an opening tag and its attributes for later rule checks."""
        line, _ = self.getpos()
        elem = Element(
            tag=tag.lower(),
            attrs={k.lower(): (v or "") for k, v in attrs},
            line=line,
            parent=self.stack[-1],
        )
        self.stack[-1].children.append(elem)
        # Void elements never push onto the stack — they would otherwise leak
        # if the source forgets a trailing ``/``.
        if tag.lower() not in VOID_ELEMENTS:
            self.stack.append(elem)

    def handle_endtag(self, tag: str) -> None:
        # Pop until we hit a matching open tag (or the root). This handles
        # documents with mismatched closes without raising.
        """Record a closing tag for structural (nesting / heading) checks."""
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag.lower():
                del self.stack[i:]
                return

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Self-closing form (``<br />``); treat as a leaf.
        """Record a self-closing tag (e.g. ``<img/>``, ``<input/>``)."""
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_ELEMENTS:
            self.stack.pop()

    def handle_data(self, data: str) -> None:
        # Append text to the *currently open* element. Whitespace-only text
        # outside any element is ignored.
        """Accumulate visible text for rules that inspect element content."""
        if self.stack and data.strip():
            self.stack[-1].text += data


def walk(elem: Element) -> Iterator[Element]:
    """
    Depth-first iterator over every descendant of ``elem`` (excluding the root).

    Parameters
    ----------
    elem : Element
        Root of the subtree to traverse.

    Yields
    ------
    Element
        Each descendant in document order.
    """
    for child in elem.children:
        yield child
        yield from walk(child)


def accessible_name(elem: Element) -> str:
    """
    Best-effort accessible name for an element.

    The function picks the first non-empty source from:

    1. ``aria-label`` (explicit override).
    2. ``title`` (tooltip fallback).
    3. Concatenated text content of the element AND every descendant.
       This is what a screen reader announces by default — the simple
       direct-text-only view misses the common ``<a><span>Label</span></a>``
       shape.
    4. ``aria-labelledby``, whose value is returned as it stands. It names
       ids rather than words, so it comes last: every caller but the
       ``<dialog>`` one only asks whether a name exists, and that one
       compares words, which an id must not shadow.

    Parameters
    ----------
    elem : Element
        Element under inspection.

    Returns
    -------
    str
        The accessible name, or ``""`` when none is present.
    """
    for attr in ("aria-label", "title"):
        if elem.attrs.get(attr, "").strip():
            return elem.attrs[attr].strip()

    # Aggregate text from this element and every descendant.
    parts: list[str] = [elem.text]
    parts.extend(d.text for d in walk(elem))
    name = " ".join(p.strip() for p in parts if p and p.strip()).strip()
    return name or elem.attrs.get("aria-labelledby", "").strip()


def has_descendant(elem: Element, tag: str) -> bool:
    """Return ``True`` when ``elem`` contains any descendant of ``tag``."""
    return any(d.tag == tag for d in walk(elem))


# ── Rule implementations ──────────────────────────────────────────────────

def check_html_lang(root: Element) -> list[Finding]:
    """Rule ``html-missing-lang`` — the ``<html>`` element must declare ``lang``."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag == "html" and not elem.attrs.get("lang", "").strip():
            findings.append(Finding(
                rule="html-missing-lang",
                line=elem.line,
                message="<html> missing required lang attribute.",
            ))
    return findings


def _has_redundant_aria(elem: Element) -> bool:
    """An ``<img alt="">`` that also carries a redundant role or aria-hidden."""
    return (
        elem.tag == "img"
        and elem.attrs.get("alt") == ""
        and (
            elem.attrs.get("role", "") == "presentation"
            or elem.attrs.get("aria-hidden", "") == "true"
        )
    )


def check_img(root: Element) -> list[Finding]:
    """Rules ``img-missing-alt`` and ``img-redundant-aria``."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag != "img":
            continue
        if "alt" not in elem.attrs:
            findings.append(Finding(
                rule="img-missing-alt",
                line=elem.line,
                message='<img> missing alt attribute. Use alt="" for decorative images.',
            ))
            continue
        # ``role="presentation"`` and ``aria-hidden`` are redundant with
        # an explicit empty ``alt`` per W3C / WAI guidance.
        if _has_redundant_aria(elem):
            findings.append(Finding(
                rule="img-redundant-aria",
                line=elem.line,
                message='Decorative <img alt="">: drop role="presentation" / aria-hidden="true" (redundant).',
            ))
    return findings


def check_links(root: Element) -> list[Finding]:
    """Rules ``a-missing-href`` and ``a-empty``."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag != "a":
            continue
        # ``<a>`` without ``href`` is not a link — it has no role, no
        # keyboard handling. Use ``<button>``.
        if "href" not in elem.attrs:
            findings.append(Finding(
                rule="a-missing-href",
                line=elem.line,
                message="<a> without href is not a link. Use <button>.",
            ))
        # An empty link has no accessible name and no destination preview.
        if not accessible_name(elem) and not has_descendant(elem, "img"):
            findings.append(Finding(
                rule="a-empty",
                line=elem.line,
                message="<a> has no accessible name.",
            ))
    return findings


def check_buttons(root: Element) -> list[Finding]:
    """Rule ``button-empty``: every ``<button>`` needs an accessible name."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag != "button":
            continue
        if not accessible_name(elem) and not has_descendant(elem, "img") and not has_descendant(elem, "svg"):
            findings.append(Finding(
                rule="button-empty",
                line=elem.line,
                message="<button> has no accessible name. Add text or aria-label.",
            ))
    return findings


def check_divspan_onclick(root: Element) -> list[Finding]:
    """Rule ``div-onclick``: ``<div>`` / ``<span>`` with ``onclick`` must be a button."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag not in {"div", "span"}:
            continue
        if "onclick" not in elem.attrs:
            continue
        # If the author opted into ``role="button"`` and a ``tabindex``,
        # they've at least done the keyboard / AT plumbing. Still suboptimal
        # vs. a real <button> but not a violation worth flagging.
        if elem.attrs.get("role", "") == "button" and "tabindex" in elem.attrs:
            continue
        findings.append(Finding(
            rule="div-onclick",
            line=elem.line,
            message=f"<{elem.tag}> with onclick: prefer <button>, or add role=\"button\" + tabindex.",
        ))
    return findings


def check_input_label(root: Element) -> list[Finding]:
    """Rule ``input-missing-label``: every focusable ``<input>`` needs a label."""
    findings: list[Finding] = []
    # Collect every ``for=...`` so we can answer "is this input referenced?".
    referenced_ids: set[str] = set()
    for elem in walk(root):
        if elem.tag == "label" and elem.attrs.get("for", "").strip():
            referenced_ids.add(elem.attrs["for"].strip())

    for elem in walk(root):
        if elem.tag != "input":
            continue
        # Hidden / submit / button / image inputs don't need a label.
        if elem.attrs.get("type", "text").lower() in {
            "hidden", "submit", "button", "reset", "image",
        }:
            continue
        # A wrapped <label><input/></label> is fine — walk parents.
        wrapped: bool = False
        parent = elem.parent
        while parent is not None and parent.tag != "root":
            if parent.tag == "label":
                wrapped = True
                break
            parent = parent.parent

        if wrapped:
            continue
        if elem.attrs.get("id", "") in referenced_ids:
            continue
        if elem.attrs.get("aria-label", "").strip():
            continue
        if elem.attrs.get("aria-labelledby", "").strip():
            continue
        findings.append(Finding(
            rule="input-missing-label",
            line=elem.line,
            message="<input> has no associated <label>, no aria-label and no aria-labelledby.",
        ))
    return findings


def check_dialog_close(root: Element) -> list[Finding]:
    """Rule ``dialog-missing-close``: every ``<dialog>`` needs a way out."""
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag != "dialog":
            continue
        # A close button with ``value="cancel"`` is the conventional pattern;
        # the browser closes the dialog when it's clicked.
        ok: bool = False
        for descendant in walk(elem):
            if descendant.tag == "button" and (
                descendant.attrs.get("value", "") in {"cancel", "close"}
                or "autofocus" in descendant.attrs
                or accessible_name(descendant).lower() in {
                    "close", "cancel", "fermer", "annuler", "schließen",
                }
            ):
                ok = True
                break
        if not ok:
            findings.append(Finding(
                rule="dialog-missing-close",
                line=elem.line,
                message="<dialog> has no obvious close affordance (button value=cancel / autofocus / 'Close' / 'Cancel').",
            ))
    return findings


def check_tabindex_positive(root: Element) -> list[Finding]:
    """Rule ``tabindex-positive``: ``tabindex`` ≥ 1 is an anti-pattern."""
    findings: list[Finding] = []
    for elem in walk(root):
        raw = elem.attrs.get("tabindex", "").strip()
        if not raw:
            continue
        try:
            value = int(raw)
        except ValueError:
            continue
        if value >= 1:
            findings.append(Finding(
                rule="tabindex-positive",
                line=elem.line,
                message=f"<{elem.tag} tabindex=\"{value}\">: positive tabindex breaks DOM order.",
            ))
    return findings


#: Tags that can take focus, and therefore can be tabbed into.
_FOCUSABLE_TAGS: frozenset[str] = frozenset(
    {"button", "a", "input", "select", "textarea"}
)


def _is_focusable(elem: Element) -> bool:
    """Whether this element can still be reached with the Tab key.

    ``aria-hidden="true"`` is only a failure on something a keyboard can land
    on: the user tabs into a control that announces nothing. Paired with
    ``tabindex="-1"`` it is the opposite — the documented way to hide the
    *second* copy of a link that already exists next to it, which is what a
    card with both a thumbnail link and a title link needs.

    This rule flagged seventeen such pairs on one blog index, every one of them
    correct, and ``--fix`` would have stripped the ``aria-hidden`` from all of
    them and made a screen reader announce every article twice. A linter whose
    automatic repair damages correct markup is worse than a missing rule.

    Four ways out of the tab order are recognised: ``tabindex="-1"``,
    ``disabled`` on a form control, ``inert``, and an ``<a>`` with no ``href``,
    which is not a link at all.
    """
    if elem.attrs.get("tabindex", "").strip() == "-1":
        return False
    if "inert" in elem.attrs:
        return False
    if elem.tag == "a":
        return bool(elem.attrs.get("href", "").strip())
    return "disabled" not in elem.attrs


def _hides_a_focusable_control(elem: Element) -> bool:
    """A control a keyboard can reach, marked ``aria-hidden="true"``."""
    return (
        elem.tag in _FOCUSABLE_TAGS
        and elem.attrs.get("aria-hidden", "") == "true"
        and _is_focusable(elem)
    )


def check_aria_hidden_interactive(root: Element) -> list[Finding]:
    """Rule ``aria-hidden-interactive``: hidden interactive elements are unreachable."""
    findings: list[Finding] = []
    for elem in walk(root):
        if not _hides_a_focusable_control(elem):
            continue
        findings.append(Finding(
            rule="aria-hidden-interactive",
            line=elem.line,
            message=(
                f'<{elem.tag} aria-hidden="true"> is still in the tab order: '
                f"a keyboard lands on a control that announces nothing. Add "
                f'tabindex="-1" if it is a duplicate of a neighbouring control.'
            ),
        ))
    return findings


HEADING_TAGS: tuple[str, ...] = ("h1", "h2", "h3", "h4", "h5", "h6")


def check_heading_order(root: Element) -> list[Finding]:
    """Rule ``heading-skip``: heading levels must not skip downward."""
    findings: list[Finding] = []
    previous: int = 0
    for elem in walk(root):
        if elem.tag not in HEADING_TAGS:
            continue
        current: int = HEADING_TAGS.index(elem.tag) + 1
        # Skipping *up* is fine (h3 → h2). Skipping *down* by more than one
        # is the anti-pattern (h2 → h4 skips h3).
        if previous and current > previous + 1:
            findings.append(Finding(
                rule="heading-skip",
                line=elem.line,
                message=f"<{elem.tag}> follows <h{previous}>: heading levels skip downward.",
            ))
        previous = current
    return findings


# Compiled patterns reused across calls.
_COLOR_STATE_PAT: re.Pattern[str] = re.compile(
    r"(?:text|bg|border|ring)-(?:red|green|emerald|rose|crimson)-\d+"
)
_MOTION_PAT: re.Pattern[str] = re.compile(
    r"\b(animate-(?:spin|ping|pulse|bounce)|transition-transform|transition-all)\b"
)
_MOTION_REDUCE_PAT: re.Pattern[str] = re.compile(r"motion-reduce:")
_TIGHT_TRACKING_PAT: re.Pattern[str] = re.compile(r"\btracking-tight(?:er)?\b")

#: Type big enough to be display rather than running text. Tailwind's scale
#: puts ``text-3xl`` at 30px; the arbitrary form ``text-[34px]`` is read too,
#: because a design system that pins exact sizes should not lose the
#: exemption for doing so.
_DISPLAY_SIZE_PAT: re.Pattern[str] = re.compile(
    r"\btext-(?:[3-9]xl|[1-9][0-9]*xl)\b|\btext-\[(\d+(?:\.\d+)?)(px|rem)\]"
)


def _is_display_type(cls: str) -> bool:
    """Whether these Tailwind classes describe display type, not running text.

    The tracking rule's evidence is about *continuous reading*: narrower
    letter-spacing slows dyslexic readers through a paragraph. A 4xl figure in
    a dashboard tile is not a paragraph — it is one glance — and tightening it
    is ordinary typography rather than a readability cost.

    The rule's docstring already promised this exemption for headings and nav
    labels; it could not see it inside a ``<p>``. A KPI number marked up as a
    paragraph is the common case, and it is what made this package's own
    sibling fail its own lint.
    """
    match = _DISPLAY_SIZE_PAT.search(cls)
    if match is None:
        return False
    if match.group(1) is None:
        return True  # a named step, text-3xl and up
    size = float(match.group(1))
    return size >= (30.0 if match.group(2) == "px" else 1.875)

#: Elements that carry continuous body text a reader scans line by line, as
#: opposed to a short heading or label read as one glance. Zorzi et al.
#: (2012) found dyslexic children read 20% faster once letter-spacing was
#: widened, not narrowed, across a paragraph of running text; the same
#: negative-tracking utility on a one-line heading has no comparable evidence
#: of harm, so headings, buttons, and nav labels are deliberately excluded.
BODY_TEXT_TAGS: frozenset[str] = frozenset({
    "p", "li", "dd", "blockquote", "td", "figcaption",
})


def check_color_only_state(root: Element) -> list[Finding]:
    """Rule ``color-only-state``: a red/green token alone is not a state cue."""
    findings: list[Finding] = []
    for elem in walk(root):
        cls: str = elem.attrs.get("class", "")
        if not _COLOR_STATE_PAT.search(cls):
            continue
        # Skip if the element has accompanying text or icon content; a state
        # banner with an icon + label is fine.
        if elem.text.strip():
            continue
        if has_descendant(elem, "svg") or has_descendant(elem, "img"):
            continue
        findings.append(Finding(
            rule="color-only-state",
            line=elem.line,
            message=f"<{elem.tag}> uses a red/green token but has no icon or text. State must not rely on color alone.",
        ))
    return findings


def _animates_unguarded(elem: Element) -> bool:
    """An animation class with no ``motion-reduce:`` peer on the same element."""
    cls: str = elem.attrs.get("class", "")
    return bool(_MOTION_PAT.search(cls)) and not _MOTION_REDUCE_PAT.search(cls)


def check_motion_reduce(root: Element) -> list[Finding]:
    """Rule ``motion-no-reduce-guard``: animations need a reduced-motion peer."""
    findings: list[Finding] = []
    for elem in walk(root):
        if not _animates_unguarded(elem):
            continue
        findings.append(Finding(
            rule="motion-no-reduce-guard",
            line=elem.line,
            message=f"<{elem.tag}> animates without a motion-reduce: peer (prefers-reduced-motion ignored).",
        ))
    return findings


def _is_tight_body_text(elem: Element) -> bool:
    """Running text set with ``tracking-tight`` or ``tracking-tighter``."""
    cls: str = elem.attrs.get("class", "")
    return (
        elem.tag in BODY_TEXT_TAGS
        and bool(_TIGHT_TRACKING_PAT.search(cls))
        and not _is_display_type(cls)  # display type, not running text
    )


def check_body_text_tracking(root: Element) -> list[Finding]:
    """Rule ``body-text-tracking-tight``: don't narrow letter-spacing on running text.

    Static proxy for the readability finding behind WCAG 1.4.12 (Text
    Spacing): reading speed for dyslexic readers improves with *wider*
    letter-spacing on continuous text, not narrower. Flags Tailwind's
    ``tracking-tight``/``tracking-tighter`` (negative ``letter-spacing``)
    only on elements that carry a paragraph's worth of running text
    (:data:`BODY_TEXT_TAGS`) — the same utility on a heading or nav label is
    a display-type choice with no comparable evidence of harm and is not
    flagged. Nor is display *type*: a ``<p>`` set at ``text-3xl`` or larger is
    a figure in a tile, not a paragraph, and the evidence behind this rule is
    about continuous reading. That exemption was promised by this docstring
    before it was implemented, and the gap made a sibling package's own
    shipped card fail this lint for a KPI number.

    **Known limit**: this only catches the Tailwind utility class;
    a literal ``letter-spacing`` CSS declaration in a ``<style>`` block or
    external stylesheet is invisible to this static, class-attribute-only
    check.
    """
    findings: list[Finding] = []
    for elem in walk(root):
        if not _is_tight_body_text(elem):
            continue
        findings.append(Finding(
            rule="body-text-tracking-tight",
            line=elem.line,
            message=f"<{elem.tag}> uses tracking-tight/tighter on running text: "
                    "narrow letter-spacing slows reading for dyslexic readers.",
        ))
    return findings


# ── Reading comfort: dyslexia and other reading difficulties ───────────────
#
# Seven rules, all warnings, all about one question: does the page set its
# running text the way the evidence says a dyslexic reader reads best?
#
# Sources, cited once here and per rule below:
#
# * WCAG 2.2 success criterion 1.4.8 Visual Presentation (level AAA): blocks of
#   text are not justified, are no wider than 80 characters, and have a line
#   spacing of at least space-and-a-half within paragraphs. Failure technique
#   F88 is "using text that is justified".
# * British Dyslexia Association, Dyslexia Style Guide (2023 edition; the
#   layout and emphasis rules are unchanged from earlier editions): left
#   aligned with a ragged right edge; avoid underlining and italics, which make
#   the text "appear to run together", and use bold instead; avoid text in
#   block capitals; line spacing of 1.5; lines of 60 to 70 characters.
# * Rello & Baeza-Yates (2013), "Good fonts for dyslexia", ASSETS '13: italic
#   type significantly impaired reading performance for readers with dyslexia
#   (eye-tracking, 48 participants).
#
# What is NOT here, on purpose: a rule asking for a "dyslexia font". Wery &
# Diliberto (2017, Annals of Dyslexia) found no gain in reading rate or
# accuracy with OpenDyslexic, and Kuster et al. (2018, Annals of Dyslexia) none
# with Dyslexie. A linter that demanded one would enforce a myth.
#
# The cascade is read the way a browser would read it, within what a static
# linter can see: Tailwind utilities on the element and its ancestors (with
# their breakpoint prefixes), ``style=""`` attributes, legacy ``align=``, the
# default italic of ``<em>``/``<i>``/``<cite>``, and simple selectors in the
# page's own ``<style>`` blocks. A linked stylesheet is not read.

#: A passage at least this many words long is "running text" for the italic,
#: capitals, justification and line-height rules. Fifteen words is more than
#: one line on a phone and roughly one line at a comfortable desktop measure,
#: which is where the evidence starts to apply: one glance at a short label is
#: not continuous reading.
LONG_PASSAGE_WORDS: int = 15

#: A centred paragraph is flagged from this many words. Higher than
#: :data:`LONG_PASSAGE_WORDS` on purpose: a centred lead of one or two lines
#: under a hero heading is a settled convention, and the cost the BDA names
#: (a ragged left edge, so each new line starts somewhere else) grows with the
#: number of lines. Thirty words is about three lines at 70 characters.
CENTERED_LONG_WORDS: int = 30

#: WCAG 1.4.8: "width is no more than 80 characters or glyphs".
MAX_LINE_CHARS: int = 80

#: WCAG 1.4.8 and the BDA: line spacing of at least 1.5 within paragraphs.
MIN_LINE_HEIGHT: float = 1.5

#: Average advance of one character of running text, in ``em``. Measured
#: Latin text in common sans faces sits between 0.45 and 0.5 em per character
#: including the space; the upper end is taken, so a width converted to
#: characters is never overestimated and the line-length rule errs quiet.
AVG_CHAR_EM: float = 0.5

#: Tailwind breakpoints, mobile first, and the widest viewport each one covers.
#: ``None`` is "no upper bound" (2xl and wider).
_BREAKPOINTS: tuple[str, ...] = ("", "sm", "md", "lg", "xl", "2xl")
_BP_INDEX: dict[str, int] = {name: i for i, name in enumerate(_BREAKPOINTS)}
_BP_VIEWPORT_MAX_PX: tuple[float | None, ...] = (640.0, 768.0, 1024.0, 1280.0, 1536.0, None)
_BP_MIN_PX: tuple[float, ...] = (0.0, 640.0, 768.0, 1024.0, 1280.0, 1536.0)

#: Variants that do not change typography or layout, read as if absent.
_NEUTRAL_VARIANTS: frozenset[str] = frozenset({"dark"})

#: Tailwind v3 default font sizes, in px, with the line height each one sets
#: on the same element (also px). ``text-sm`` is 14px on a 20px line: 1.43,
#: under 1.5 — a fact of Tailwind's defaults that the leading rule reports.
_FONT_SIZES: dict[str, tuple[float, float | None]] = {
    "xs": (12.0, 16.0), "sm": (14.0, 20.0), "base": (16.0, 24.0),
    "lg": (18.0, 28.0), "xl": (20.0, 28.0), "2xl": (24.0, 32.0),
    "3xl": (30.0, 36.0), "4xl": (36.0, 40.0), "5xl": (48.0, None),
    "6xl": (60.0, None), "7xl": (72.0, None), "8xl": (96.0, None), "9xl": (128.0, None),
}
_LEADING_RATIOS: dict[str, float] = {
    "none": 1.0, "tight": 1.25, "snug": 1.375, "normal": 1.5, "relaxed": 1.625, "loose": 2.0,
}
_MAX_W_REM: dict[str, float] = {
    "xs": 20, "sm": 24, "md": 28, "lg": 32, "xl": 36, "2xl": 42, "3xl": 48,
    "4xl": 56, "5xl": 64, "6xl": 72, "7xl": 80,
}
_SCREEN_PX: dict[str, float] = {"sm": 640, "md": 768, "lg": 1024, "xl": 1280, "2xl": 1536}
_FRACTION_RE: re.Pattern[str] = re.compile(r"^(?:w|basis)-(\d+)/(\d+)$")
_LENGTH_RE: re.Pattern[str] = re.compile(r"^(-?\d*\.?\d+)(px|rem|em|ch|%)?$")

#: Elements a browser sets in italic, underlined or centred by default.
_ITALIC_TAGS: frozenset[str] = frozenset({"em", "i", "cite", "dfn", "var", "address"})
_UNDERLINE_TAGS: frozenset[str] = frozenset({"u"})
#: Subtrees whose text a sighted reader does not read as page prose.
_NON_PROSE_TAGS: frozenset[str] = frozenset({
    "script", "style", "template", "noscript", "svg", "math", "code", "pre", "kbd", "samp",
})
#: Block containers that end a running-text unit: the text inside them is
#: counted for the inner element, not again for the outer one.
_BLOCK_TAGS: frozenset[str] = frozenset({
    "div", "section", "article", "aside", "header", "footer", "main", "nav",
    "ul", "ol", "dl", "table", "figure", "form", "details", "fieldset",
    "h1", "h2", "h3", "h4", "h5", "h6",
}) | BODY_TEXT_TAGS


Value = Any  # a typed CSS value: str, float, or ("ratio"|"px", float)


@dataclass
class _CssRule:
    """One rule from a ``<style>`` block, reduced to what the reading rules read."""

    selector: list[tuple[str, str, frozenset[str], str]]  # (combinator, tag, classes, id)
    specificity: tuple[int, int, int]
    order: int
    decls: dict[str, Value]


def _split_variants(token: str) -> tuple[list[str], str]:
    """Split ``md:dark:text-justify`` into variants and the base utility.

    A colon inside an arbitrary value (``text-[color:red]``) is not a variant
    separator, hence the lookahead.
    """
    parts = re.split(r":(?![^\[]*\])", token)
    return parts[:-1], parts[-1].lstrip("!")


def _utilities(elem: Element) -> list[tuple[int, str]]:
    """Every class of ``elem`` that applies at some breakpoint, with its index.

    A state variant (``hover:``, ``focus:``, ``group-hover:``) is dropped: the
    reading rules judge the text at rest, which is how it is read.
    """
    out: list[tuple[int, str]] = []
    for token in elem.attrs.get("class", "").split():
        variants, base = _split_variants(token)
        bp = 0
        keep = True
        for variant in variants:
            if variant in _BP_INDEX:
                bp = max(bp, _BP_INDEX[variant])
            elif variant not in _NEUTRAL_VARIANTS:
                keep = False
        if keep:
            out.append((bp, base))
    return out


def _length_px(value: str, font_px: float) -> float | None:
    """A CSS length in px, or ``None`` when it is relative to something unseen."""
    match = _LENGTH_RE.match(value.strip())
    if match is None:
        return None
    number, unit = float(match.group(1)), (match.group(2) or "")
    if unit == "px":
        return number
    if unit == "rem":
        return number * 16.0
    if unit == "em":
        return number * font_px
    if unit == "ch":
        # One ``ch`` is read as one character of text: the unit's purpose,
        # and how every "65ch" measure is meant.
        return number * AVG_CHAR_EM * font_px
    return None


def _tw_value(base: str) -> tuple[str, Value] | None:
    """The reading-relevant property a Tailwind utility sets, or ``None``."""
    align = {
        "text-left": "left", "text-start": "left", "text-right": "right",
        "text-end": "right", "text-center": "center", "text-justify": "justify",
    }
    if base in align:
        return "text-align", align[base]
    if base == "italic":
        return "font-style", "italic"
    if base == "not-italic":
        return "font-style", "normal"
    if base == "uppercase":
        return "text-transform", "uppercase"
    if base in ("lowercase", "capitalize", "normal-case"):
        return "text-transform", "none"
    if base == "underline":
        return "text-decoration", "underline"
    if base in ("no-underline", "line-through", "overline"):
        return "text-decoration", "none"
    if base.startswith("leading-"):
        key = base[len("leading-"):]
        if key in _LEADING_RATIOS:
            return "line-height", ("ratio", _LEADING_RATIOS[key])
        if key.isdigit():
            return "line-height", ("px", int(key) * 4.0)
        if key.startswith("[") and key.endswith("]"):
            parsed = _css_decls(f"line-height:{key[1:-1]}").get("line-height")
            return ("line-height", parsed) if parsed is not None else None
    return None


def _tw_font(base: str) -> tuple[float, Value | None] | None:
    """Font size in px set by a ``text-*`` utility, and the line height it brings.

    ``text-sm/6`` (size and line height in one utility) is read too.
    """
    match = re.fullmatch(r"text-([a-z0-9]+|\[[^\]]+\])(?:/(\d+|\[[^\]]+\]))?", base)
    if match is None:
        return None
    size_key, lead_key = match.group(1), match.group(2)
    if size_key in _FONT_SIZES:
        size, default_lead = _FONT_SIZES[size_key]
        lead: Value | None = ("px", default_lead) if default_lead is not None else ("ratio", 1.0)
    elif size_key.startswith("["):
        px = _length_px(size_key[1:-1], 16.0)
        if px is None:
            return None  # text-[color] and friends
        size, lead = px, None
    else:
        return None
    if lead_key:
        if lead_key.isdigit():
            lead = ("px", int(lead_key) * 4.0)
        else:
            lead = _css_decls(f"line-height:{lead_key[1:-1]}").get("line-height", lead)
    return size, lead


def _css_decls(text: str) -> dict[str, Value]:
    """Parse ``prop: value; …`` into the typed values the reading rules read."""
    out: dict[str, Value] = {}
    for decl in text.split(";"):
        if ":" not in decl:
            continue
        prop, _, raw = decl.partition(":")
        prop = prop.strip().lower()
        value = raw.replace("!important", "").strip().lower()
        if prop == "text-align":
            out[prop] = {"start": "left", "end": "right"}.get(value, value)
        elif prop == "font-style":
            out[prop] = "italic" if value in ("italic", "oblique") or value.startswith("oblique") else "normal"
        elif prop == "text-transform":
            out[prop] = "uppercase" if value == "uppercase" else "none"
        elif prop in ("text-decoration", "text-decoration-line"):
            out["text-decoration"] = "underline" if "underline" in value.split() else "none"
        elif prop == "line-height":
            if value == "normal":
                out[prop] = ("ratio", 1.2)  # what browsers resolve "normal" to, roughly
            else:
                try:
                    out[prop] = ("ratio", float(value))
                except ValueError:
                    if value.endswith("%"):
                        try:
                            out[prop] = ("ratio", float(value[:-1]) / 100.0)
                        except ValueError:
                            pass
                    elif value.endswith("em") and not value.endswith("rem"):
                        try:
                            out[prop] = ("ratio", float(value[:-2]))
                        except ValueError:
                            pass
                    elif _length_px(value, 16.0) is not None:
                        out[prop] = ("px", _length_px(value, 16.0))
        elif prop == "font-size":
            px = _length_px(value, 16.0)
            if px is not None:
                out[prop] = px
        elif prop in ("max-width", "width"):
            out[prop] = value
    return out


_COMPOUND_RE: re.Pattern[str] = re.compile(r"^([a-z][a-z0-9-]*|\*)?((?:[.#][\w-]+)*)$")


def _parse_selector(selector: str) -> list[tuple[str, str, frozenset[str], str]] | None:
    """A selector as compounds, or ``None`` when it is beyond this reader.

    Pseudo-classes, attribute selectors and sibling combinators make a rule
    conditional on something a static read cannot settle (a hover, a toggle
    such as the reading preset's own ``[data-text-spacing]``), so such a rule
    is left out rather than guessed at.
    """
    if any(ch in selector for ch in ":[+~"):
        return None
    tokens = selector.replace(">", " > ").split()
    compounds: list[tuple[str, str, frozenset[str], str]] = []
    combinator = " "
    for token in tokens:
        if token == ">":
            combinator = ">"
            continue
        match = _COMPOUND_RE.match(token.lower())
        if match is None:
            return None
        tag = match.group(1) or "*"
        rest = match.group(2) or ""
        classes = frozenset(re.findall(r"\.([\w-]+)", rest))
        ids = re.findall(r"#([\w-]+)", rest)
        compounds.append((combinator, tag, classes, ids[0] if ids else ""))
        combinator = " "
    return compounds or None


def _compound_matches(elem: Element, compound: tuple[str, str, frozenset[str], str]) -> bool:
    """Whether one compound selector matches ``elem`` on its own."""
    _, tag, classes, ident = compound
    if tag != "*" and elem.tag != tag:
        return False
    if classes and not classes <= set(elem.attrs.get("class", "").split()):
        return False
    return not ident or elem.attrs.get("id", "") == ident


def _selector_matches(elem: Element, compounds: list[tuple[str, str, frozenset[str], str]]) -> bool:
    """Right-to-left match of a descendant / child selector chain."""
    if not _compound_matches(elem, compounds[-1]):
        return False
    current: Element | None = elem
    for index in range(len(compounds) - 2, -1, -1):
        combinator = compounds[index + 1][0]
        assert current is not None
        current = current.parent
        if combinator == ">":
            if current is None or not _compound_matches(current, compounds[index]):
                return False
            continue
        while current is not None and not _compound_matches(current, compounds[index]):
            current = current.parent
        if current is None:
            return False
    return True


def _style_rules(root: Element) -> tuple[list[_CssRule], bool]:
    """Every rule of the page's ``<style>`` blocks, and whether all were read.

    The second value is ``False`` when a rule that sets a width could not be
    parsed, or when a stylesheet is linked: then the page's widths are not
    all visible, and "no width limit" cannot be proven.
    """
    rules: list[_CssRule] = []
    complete = True
    order = 0
    for elem in walk(root):
        if elem.tag == "link" and "stylesheet" in elem.attrs.get("rel", "").lower().split():
            complete = False
        if elem.tag != "style":
            continue
        css = re.sub(r"/\*.*?\*/", "", elem.text, flags=re.S)
        if "@import" in css:
            complete = False
        # Drop print-only and keyframe blocks; unwrap every other at-rule, so
        # a rule inside @media (min-width: …) counts as applying somewhere.
        css = re.sub(r"@(?:media\s+print|keyframes|-webkit-keyframes|font-face)[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
        css = re.sub(r"@[^{;]*\{", "", css)
        for selector_text, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            decls = _css_decls(body)
            if not decls:
                continue
            for selector in selector_text.split(","):
                compounds = _parse_selector(selector.strip())
                if compounds is None:
                    if "max-width" in decls or "width" in decls:
                        complete = False
                    continue
                spec = (
                    sum(1 for c in compounds if c[3]),
                    sum(len(c[2]) for c in compounds),
                    sum(1 for c in compounds if c[1] != "*"),
                )
                rules.append(_CssRule(compounds, spec, order, decls))
                order += 1
    return rules, complete


class _Cascade:
    """The values a browser would compute for one page, as far as source shows.

    Built once per page and memoised per (element, property, breakpoint): the
    rules ask the same ancestors the same questions many times over.
    """

    def __init__(self, root: Element) -> None:
        """Read the page's ``<style>`` rules and remember the root."""
        self.root = root
        self.rules, self.widths_visible = _style_rules(root)
        self._own: dict[tuple[int, str, int], Value | None] = {}

    def own(self, elem: Element, prop: str, bp: int) -> Value | None:
        """The value ``elem`` sets itself for ``prop`` at breakpoint ``bp``."""
        key = (id(elem), prop, bp)
        if key not in self._own:
            self._own[key] = self._compute_own(elem, prop, bp)
        return self._own[key]

    def _compute_own(self, elem: Element, prop: str, bp: int) -> Value | None:
        # 1. Inline style wins over everything this reader can see.
        inline = _css_decls(elem.attrs.get("style", ""))
        if prop in inline:
            return inline[prop]
        # 2. Tailwind utilities: the widest breakpoint at or below ``bp`` wins.
        best: tuple[int, Value] | None = None
        for at, base in _utilities(elem):
            if at > bp:
                continue
            value: Value | None = None
            if prop in ("font-size", "line-height"):
                font = _tw_font(base)
                if font is not None:
                    if prop == "font-size":
                        value = font[0]
                    elif font[1] is not None:
                        value = font[1]
            if value is None:
                hit = _tw_value(base)
                if hit is not None and hit[0] == prop:
                    value = hit[1]
            # A ``leading-*`` beats the line height a ``text-*`` brings, at any
            # breakpoint at or below: Tailwind emits the leading utilities later.
            if value is not None and (best is None or at >= best[0]):
                if prop == "line-height" and best is not None and at == best[0] and base.startswith("text-"):
                    continue
                best = (at, value)
        tw_value = best[1] if best else None
        # 3. The page's own <style> rules, by specificity then order. A rule
        #    with more than a class's specificity beats a utility.
        css_best: _CssRule | None = None
        for rule in self.rules:
            if prop in rule.decls and _selector_matches(elem, rule.selector):
                if css_best is None or (rule.specificity, rule.order) >= (css_best.specificity, css_best.order):
                    css_best = rule
        if css_best is not None and (tw_value is None or css_best.specificity > (0, 1, 0)):
            return css_best.decls[prop]
        if tw_value is not None:
            return tw_value
        # 4. Legacy attributes and the browser's own defaults.
        if prop == "text-align":
            align = elem.attrs.get("align", "").lower()
            if align in ("justify", "center", "left", "right"):
                return align
            if elem.tag == "center":
                return "center"
        if prop == "font-style" and elem.tag in _ITALIC_TAGS:
            return "italic"
        if prop == "text-decoration" and elem.tag in _UNDERLINE_TAGS:
            return "underline"
        return None

    def computed(self, elem: Element, prop: str, bp: int) -> Value | None:
        """The inherited value: the nearest element, self first, that sets it."""
        current: Element | None = elem
        while current is not None and current.tag != "root":
            value = self.own(current, prop, bp)
            if value is not None:
                return value
            current = current.parent
        return None

    def font_px(self, elem: Element, bp: int) -> float:
        """The font size in px, 16 when nothing sets it."""
        value = self.computed(elem, "font-size", bp)
        return float(value) if isinstance(value, (int, float)) else 16.0

    def line_height_ratio(self, elem: Element, bp: int) -> tuple[float, Element | None] | None:
        """Line height over font size, and the element that set it.

        Line height inherits as declared for a ratio but as computed for a
        length, so a ``leading-6`` on a wrapper is 24px for every child; the
        ratio is that length over the child's own font size.
        """
        current: Element | None = elem
        while current is not None and current.tag != "root":
            value = self.own(current, "line-height", bp)
            if value is not None:
                kind, number = value
                if kind == "ratio":
                    return float(number), current
                return float(number) / self.font_px(elem, bp), current
            current = current.parent
        return None


def _visible(elem: Element) -> bool:
    """Whether ``elem``'s text is painted for a sighted reader."""
    if elem.tag in _NON_PROSE_TAGS or "hidden" in elem.attrs:
        return False
    return "sr-only" not in elem.attrs.get("class", "").split()


def _shown(elem: Element) -> bool:
    """Whether ``elem`` and every ancestor are painted."""
    return _visible(elem) and all(_visible(a) for a in _ancestors(elem))


def _words(elem: Element, stop: Callable[[Element], bool]) -> list[str]:
    """Visible words of ``elem``'s subtree, not descending into ``stop`` subtrees."""
    if not _visible(elem):
        return []
    words = elem.text.split()
    for child in elem.children:
        if stop(child) or not _visible(child):
            continue
        words.extend(_words(child, stop))
    return words


def _unit_words(elem: Element) -> list[str]:
    """The words of one running-text unit, without the blocks nested inside it."""
    return _words(elem, lambda child: child.tag in _BLOCK_TAGS)


def _running_units(root: Element, cascade: _Cascade, min_words: int) -> Iterator[tuple[Element, list[str]]]:
    """Running-text elements of at least ``min_words`` words, display type excluded.

    A unit is one of :data:`BODY_TEXT_TAGS`. Display type (30px and up, the
    same line the tracking rule draws) is a figure in a tile, not a passage.
    """
    for elem in walk(root):
        if elem.tag not in BODY_TEXT_TAGS or not _shown(elem):
            continue
        words = _unit_words(elem)
        if len(words) < min_words:
            continue
        if cascade.font_px(elem, len(_BREAKPOINTS) - 1) >= 30.0:
            continue
        yield elem, words


def _first_bp(predicate: Callable[[int], bool]) -> int | None:
    """The narrowest breakpoint at which ``predicate`` holds, or ``None``."""
    for bp in range(len(_BREAKPOINTS)):
        if predicate(bp):
            return bp
    return None


def _at(bp: int) -> str:
    """How a finding names the screen width it is about."""
    return "" if bp == 0 else f" on screens {_BP_MIN_PX[bp]:.0f}px wide and up"


def _excerpt(words: list[str], n: int = 8) -> str:
    """The first few words, so a finding says which passage it means."""
    text = " ".join(words[:n]).strip("“”«»\"' \u00a0")
    return f"“{text}{'…' if len(words) > n else ''}”"


def check_reading_alignment(root: Element) -> list[Finding]:
    """Rules ``body-text-justified`` and ``body-text-centered-long``.

    Justified text stretches the spaces between words to square both edges,
    and on a screen, with no hyphenation to absorb the slack, those gaps line
    up into "rivers" running down the paragraph. WCAG 1.4.8 (AAA) asks that a
    block of text not be justified, and failure technique F88 names exactly
    this. The BDA style guide asks for "left-justified with ragged right edge".

    Centred text has the opposite fault: a ragged *left* edge, so each new
    line begins at a different place and the eye has to search for it. The
    BDA guide's left alignment covers it too; it is reported from
    :data:`CENTERED_LONG_WORDS`, because a one or two line centred lead under a
    hero heading is a settled convention and costs one search, not ten.

    **Known limit**: alignment set in a linked stylesheet is not seen; a page
    whose ``<style>`` uses a selector this reader skips (pseudo-classes,
    attributes) is not seen through it either.
    """
    cascade = _cascade_for(root)
    findings: list[Finding] = []
    for elem, words in _running_units(root, cascade, LONG_PASSAGE_WORDS):
        justified = _first_bp(lambda bp: cascade.computed(elem, "text-align", bp) == "justify")
        if justified is not None:
            findings.append(Finding(
                rule="body-text-justified",
                line=elem.line,
                message=(
                    f"<{elem.tag}> {_excerpt(words)} is justified{_at(justified)}: the stretched "
                    "word spaces form rivers that dyslexic readers lose their line in. "
                    "Align it left (WCAG 1.4.8, BDA style guide)."
                ),
            ))
            continue
        if len(words) < CENTERED_LONG_WORDS:
            continue
        centred = _first_bp(lambda bp: cascade.computed(elem, "text-align", bp) == "center")
        if centred is not None:
            findings.append(Finding(
                rule="body-text-centered-long",
                line=elem.line,
                message=(
                    f"<{elem.tag}> {_excerpt(words)} is centred over {len(words)} words{_at(centred)}: "
                    "every line starts somewhere else. Align running text left (BDA style guide)."
                ),
            ))
    return findings


def _starts_here(cascade: _Cascade, elem: Element, prop: str, value: str, bp: int) -> bool:
    """``elem`` turns ``prop`` to ``value`` at ``bp`` while its parent does not."""
    if cascade.computed(elem, prop, bp) != value:
        return False
    parent = elem.parent
    return parent is None or parent.tag == "root" or cascade.computed(parent, prop, bp) != value


def _styled_runs(root: Element, prop: str, value: str) -> Iterator[tuple[Element, int, list[str]]]:
    """Each outermost element where ``prop`` becomes ``value``, with its words.

    The words counted are the ones the style actually reaches: a descendant
    that turns it off again (``not-italic``, ``normal-case``) is not counted.
    """
    cascade = _cascade_for(root)
    for elem in walk(root):
        if not _shown(elem):
            continue
        for bp in range(len(_BREAKPOINTS)):
            if not _starts_here(cascade, elem, prop, value, bp):
                continue
            at = bp

            def turned_off(child: Element) -> bool:
                """A descendant that sets the property back to something else."""
                return cascade.own(child, prop, at) not in (None, value)

            yield elem, bp, _words(elem, turned_off)
            break


def check_reading_italic(root: Element) -> list[Finding]:
    """Rule ``body-text-italic-long``: no long passage set in italic.

    Italic slants and narrows the letterforms, and the BDA style guide says it
    makes "the text appear to run together"; Rello & Baeza-Yates (2013)
    measured slower reading in italic for readers with dyslexia. Emphasis of a
    word or a title is fine — the rule counts the words the italic reaches and
    reports a passage from :data:`LONG_PASSAGE_WORDS`. Use bold, or a box, for
    a passage that must stand out.
    """
    findings: list[Finding] = []
    for elem, bp, words in _styled_runs(root, "font-style", "italic"):
        if len(words) >= LONG_PASSAGE_WORDS:
            findings.append(Finding(
                rule="body-text-italic-long",
                line=elem.line,
                message=(
                    f"<{elem.tag}> sets {len(words)} words in italic{_at(bp)}, {_excerpt(words)}: "
                    "slanted type runs together for dyslexic readers. Keep italic to a few "
                    "words; use bold for emphasis (BDA style guide)."
                ),
            ))
    return findings


def _mostly_capitals(words: list[str]) -> bool:
    """Whether the text itself is typed in capitals, not just transformed."""
    lettered = [w for w in words if sum(ch.isalpha() for ch in w) >= 2]
    capitals = [w for w in lettered if w.isupper()]
    return len(capitals) >= LONG_PASSAGE_WORDS and len(capitals) >= 0.8 * len(lettered)


def check_reading_capitals(root: Element) -> list[Finding]:
    """Rule ``body-text-all-caps-long``: no long passage in capitals.

    Text in capitals loses the ascenders and descenders that give each word
    its outline, and every word becomes a rectangle of the same height. The
    BDA style guide: "avoid text in block capitals: this is much harder to
    read". Two shapes are caught: a Tailwind ``uppercase`` (or
    ``text-transform: uppercase``) reaching :data:`LONG_PASSAGE_WORDS` words,
    and running text typed in capitals in the source. A short eyebrow label
    in capitals is not reported.
    """
    findings: list[Finding] = []
    reported: set[int] = set()
    for elem, bp, words in _styled_runs(root, "text-transform", "uppercase"):
        if len(words) >= LONG_PASSAGE_WORDS:
            reported.add(id(elem))
            findings.append(Finding(
                rule="body-text-all-caps-long",
                line=elem.line,
                message=(
                    f"<{elem.tag}> sets {len(words)} words in capitals{_at(bp)}, {_excerpt(words)}: "
                    "capitals take away the word shapes dyslexic readers lean on (BDA style guide)."
                ),
            ))
    cascade = _cascade_for(root)
    for elem, words in _running_units(root, cascade, LONG_PASSAGE_WORDS):
        if id(elem) in reported or not _mostly_capitals(words):
            continue
        if any(id(a) in reported for a in _ancestors(elem)):
            continue
        findings.append(Finding(
            rule="body-text-all-caps-long",
            line=elem.line,
            message=(
                f"<{elem.tag}> {_excerpt(words)} is typed in capitals: they take away the "
                "word shapes dyslexic readers lean on. Write it in sentence case (BDA style guide)."
            ),
        ))
    return findings


def _ancestors(elem: Element) -> Iterator[Element]:
    """Every ancestor of ``elem``, nearest first, the synthetic root excluded."""
    current = elem.parent
    while current is not None and current.tag != "root":
        yield current
        current = current.parent


def check_reading_leading(root: Element) -> list[Finding]:
    """Rule ``body-text-leading-tight``: line height under 1.5 on running text.

    WCAG 1.4.8 (AAA) asks for line spacing of at least space-and-a-half within
    paragraphs, and the BDA style guide for 1.5: lines set closer crowd one
    another, and a reader who struggles to hold their place jumps lines.

    Read from ``leading-*`` utilities (on the element or inherited), ``style``
    and ``<style>`` line heights, and the line height a Tailwind ``text-*``
    size brings with it — ``text-sm`` is 14px on a 20px line, which is 1.43,
    and ``text-xs`` and ``text-xl`` are under 1.5 too. That last case is a
    property of Tailwind's default theme: a project that redefines its font
    sizes in ``tailwind.config.js`` is judged on the defaults, because the
    config is not read. Display type is exempt, as for the tracking rule.
    """
    cascade = _cascade_for(root)
    findings: list[Finding] = []
    for elem, words in _running_units(root, cascade, LONG_PASSAGE_WORDS):
        for bp in range(len(_BREAKPOINTS)):
            resolved = cascade.line_height_ratio(elem, bp)
            if resolved is None:
                continue  # nothing set: the browser default for body text applies
            ratio, setter = resolved
            if ratio < MIN_LINE_HEIGHT - 1e-6:
                where = "" if setter is elem or setter is None else f" (set on <{setter.tag}> line {setter.line})"
                findings.append(Finding(
                    rule="body-text-leading-tight",
                    line=elem.line,
                    message=(
                        f"<{elem.tag}> {_excerpt(words)} has a line height of {ratio:.2f}{where}"
                        f"{_at(bp)}: under 1.5, lines crowd each other and a reader jumps lines "
                        "(WCAG 1.4.8, BDA style guide). Add leading-normal or leading-relaxed; "
                        "note that Tailwind's text-xs, text-sm and text-xl bring a line height "
                        "under 1.5 with them."
                    ),
                ))
                break
    return findings


def _own_width_px(cascade: _Cascade, elem: Element, bp: int) -> tuple[str, float] | None:
    """A width limit ``elem`` sets itself: ("max", px), ("fraction", f), or ("none", 0).

    ``("none", 0)`` is an explicit "no limit" (``max-w-none``, ``max-w-full``
    with nothing narrower), returned so the caller keeps climbing.
    """
    font = cascade.font_px(elem, bp)
    for source in ("inline", "tailwind", "css"):
        best: tuple[int, tuple[str, float]] | None = None
        if source == "inline":
            decls = _css_decls(elem.attrs.get("style", ""))
            for prop in ("max-width", "width"):
                if prop in decls:
                    px = _length_px(str(decls[prop]), font)
                    if px is not None:
                        return "max", px
                    if str(decls[prop]).endswith("%"):
                        try:
                            return "fraction", float(str(decls[prop])[:-1]) / 100.0
                        except ValueError:
                            pass
            continue
        if source == "tailwind":
            for at, base in _utilities(elem):
                if at > bp:
                    continue
                hit = _tw_width(base, font, bp)
                if hit is not None and (best is None or at >= best[0]):
                    best = (at, hit)
            if best is not None:
                return best[1]
            continue
        for rule in cascade.rules:
            for prop in ("max-width", "width"):
                if prop in rule.decls and _selector_matches(elem, rule.selector):
                    px = _length_px(str(rule.decls[prop]), font)
                    if px is not None:
                        return "max", px
    return None


def _tw_width(base: str, font: float, bp: int) -> tuple[str, float] | None:
    """The width limit one Tailwind utility sets, in the shape of :func:`_own_width_px`."""
    if base == "container":
        return ("max", _BP_MIN_PX[bp]) if bp > 0 else ("none", 0.0)
    if base.startswith("max-w-"):
        key = base[len("max-w-"):]
        if key in _MAX_W_REM:
            return "max", _MAX_W_REM[key] * 16.0
        if key == "prose":
            return "max", 65 * AVG_CHAR_EM * font
        if key.startswith("screen-") and key[len("screen-"):] in _SCREEN_PX:
            return "max", _SCREEN_PX[key[len("screen-"):]]
        if key in ("none", "full", "screen"):
            return "none", 0.0
        if key.startswith("[") and key.endswith("]"):
            px = _length_px(key[1:-1], font)
            return ("max", px) if px is not None else None
        return None
    match = _FRACTION_RE.match(base)
    if match is not None and int(match.group(2)):
        return "fraction", int(match.group(1)) / int(match.group(2))
    if base.startswith("w-"):
        key = base[2:]
        if key.isdigit():
            return "max", int(key) * 4.0
        if key.startswith("[") and key.endswith("]"):
            px = _length_px(key[1:-1], font)
            return ("max", px) if px is not None else None
    return None


def _padding_px(elem: Element, bp: int) -> float:
    """Horizontal padding a Tailwind ``p-*`` / ``px-*`` takes out of the width."""
    total = 0.0
    best_at = -1
    for at, base in _utilities(elem):
        match = re.fullmatch(r"p[xlr]?-(\d+(?:\.\d+)?)", base)
        if match is None or at > bp or at < best_at:
            continue
        side = 1 if base[1] in "lr" else 2
        best_at = at
        total = float(match.group(1)) * 4.0 * side
    return total


def _grid_columns(elem: Element, bp: int) -> int | None:
    """Columns of a ``grid-cols-N`` / ``columns-N`` at ``bp``; 1 when it is one column."""
    best: tuple[int, int] | None = None
    for at, base in _utilities(elem):
        match = re.fullmatch(r"(?:grid-cols|columns)-(\d+)", base)
        if match is None or at > bp:
            continue
        if best is None or at >= best[0]:
            best = (at, int(match.group(1)))
    return best[1] if best else None


def _span(elem: Element, columns: int, bp: int) -> int:
    """How many grid columns ``elem`` spans at ``bp``."""
    best: tuple[int, int] | None = None
    for at, base in _utilities(elem):
        if at > bp:
            continue
        if base == "col-span-full":
            value = columns
        else:
            match = re.fullmatch(r"col-span-(\d+)", base)
            if match is None:
                continue
            value = int(match.group(1))
        if best is None or at >= best[0]:
            best = (at, value)
    return min(best[1], columns) if best else 1


def _flex_row(elem: Element, bp: int) -> bool:
    """Whether ``elem`` lays several children side by side in a flex row at ``bp``."""
    display: tuple[int, str] | None = None
    direction: tuple[int, str] | None = None
    for at, base in _utilities(elem):
        if at > bp:
            continue
        if base in ("flex", "inline-flex", "block", "grid", "hidden", "inline-block"):
            if display is None or at >= display[0]:
                display = (at, base)
        if base in ("flex-row", "flex-col", "flex-row-reverse", "flex-col-reverse"):
            if direction is None or at >= direction[0]:
                direction = (at, base)
    if display is None or display[1] not in ("flex", "inline-flex"):
        return False
    if direction is not None and direction[1].startswith("flex-col"):
        return False
    return sum(1 for c in elem.children if c.tag not in _NON_PROSE_TAGS) >= 2


def _line_chars(cascade: _Cascade, elem: Element, bp: int) -> float | None:
    """The longest line ``elem`` can set at ``bp``, in characters.

    ``None`` when the width cannot be decided from source (a flex row shares
    it out by content). ``inf`` when nothing on the page bounds it at 2xl and
    the page's widths are all visible.
    """
    font = cascade.font_px(elem, bp)
    factor = 1.0
    padding = 0.0
    child: Element | None = None
    current: Element | None = elem
    viewport = _BP_VIEWPORT_MAX_PX[bp]
    while current is not None and current.tag != "root":
        if child is not None:
            columns = _grid_columns(current, bp)
            if columns and columns > 1:
                factor *= _span(child, columns, bp) / columns
            elif _flex_row(current, bp):
                return None
        padding += _padding_px(current, bp)
        width = _own_width_px(cascade, current, bp)
        if width is not None:
            kind, value = width
            if kind == "fraction":
                factor *= value
            elif kind == "max":
                limit = value if viewport is None else min(value, viewport)
                px = max(limit - padding, 0.0) * factor
                return px / (AVG_CHAR_EM * font)
        child = current
        current = current.parent
    if not cascade.widths_visible:
        return None  # a linked stylesheet may bound it; not provable from here
    if viewport is None:
        return float("inf")
    return max(viewport - padding, 0.0) * factor / (AVG_CHAR_EM * font)


def check_reading_line_length(root: Element) -> list[Finding]:
    """Rule ``body-text-line-too-long``: lines over 80 characters.

    WCAG 1.4.8 (AAA): "width is no more than 80 characters or glyphs". The BDA
    style guide asks for 60 to 70. A long line makes the return sweep to the
    start of the next one long too, and that sweep is where a reader who
    struggles to track lines loses their place.

    The width is worked out from source at each Tailwind breakpoint: the
    nearest ``max-w-*`` / ``w-*`` / ``container`` (or ``max-width`` in a
    ``style``), the screen width the breakpoint allows, padding taken off,
    divided by the ``grid-cols-N`` / ``columns-N`` crossed on the way, then
    turned into characters at :data:`AVG_CHAR_EM` per character of the
    element's font size. A ``max-w-prose`` (65ch) passes; ``max-w-3xl`` of
    16px text (96 characters) does not.

    **Known limits**: a flex row shares its width by content, so text inside
    one is not judged; a page that links a stylesheet may bound its text
    there, so "no limit at all" is only reported on a page whose styles are
    all in its own markup; gaps between grid columns are not subtracted, and
    an average character width is an estimate, chosen at the wide end so the
    rule errs quiet.
    """
    cascade = _cascade_for(root)
    findings: list[Finding] = []
    for elem, words in _running_units(root, cascade, 1):
        if len(" ".join(words)) <= MAX_LINE_CHARS:
            continue  # a passage shorter than a line cannot set a long one
        widths = [_line_chars(cascade, elem, bp) for bp in range(len(_BREAKPOINTS))]
        over = [bp for bp, chars in enumerate(widths) if chars is not None and chars > MAX_LINE_CHARS + 0.5]
        if not over:
            continue
        worst = max(widths[bp] or 0.0 for bp in over)
        measure = (
            "no width limit" if worst == float("inf")
            else f"lines of up to about {worst:.0f} characters"
        )
        findings.append(Finding(
            rule="body-text-line-too-long",
            line=elem.line,
            message=(
                f"<{elem.tag}> {_excerpt(words)} has {measure}{_at(over[0])}: past 80 the eye "
                "loses the next line on the way back (WCAG 1.4.8; the BDA asks 60 to 70). "
                "Bound the text with max-w-prose or max-w-[70ch]."
            ),
        ))
    return findings


def _is_link_like(elem: Element) -> bool:
    """A link, or a control a reader expects to look clickable."""
    return (
        elem.tag in ("a", "button", "summary")
        or elem.attrs.get("role", "") in ("link", "button", "tab", "menuitem")
        or "onclick" in elem.attrs
    )


def check_reading_underline(root: Element) -> list[Finding]:
    """Rule ``text-underline-not-link``: underlined text that is not a link.

    On the web an underline promises a link, so underlined plain text is a
    false promise to every reader. For a dyslexic reader it also costs
    reading: the BDA style guide asks to "avoid underlining and italics: these
    tend to make the text appear to run together", since the rule cuts through
    the descenders. Reported for a Tailwind ``underline`` at rest (not
    ``hover:underline``), a ``text-decoration: underline`` and a ``<u>``, when
    neither the element nor an ancestor is a link or a control and it holds
    no link. ``<abbr>`` keeps its dotted underline: that one is the browser's,
    and it means "there is an expansion here".
    """
    cascade = _cascade_for(root)
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag == "abbr" or _is_link_like(elem) or not _shown(elem):
            continue
        if not any(
            cascade.own(elem, "text-decoration", bp) == "underline"
            for bp in range(len(_BREAKPOINTS))
        ):
            continue
        if any(_is_link_like(a) for a in _ancestors(elem)):
            continue
        if any(_is_link_like(d) for d in walk(elem)):
            continue
        words = _words(elem, lambda child: False)
        if not words:
            continue
        findings.append(Finding(
            rule="text-underline-not-link",
            line=elem.line,
            message=(
                f"<{elem.tag}> {_excerpt(words)} is underlined but is not a link: readers "
                "will try to click it, and the line runs through the letters. Use bold "
                "for emphasis (BDA style guide)."
            ),
        ))
    return findings


#: One cascade per parsed page, shared by the seven reading rules. Keyed by
#: the root's identity and holding the root itself, so an id is never reused
#: for another page while its entry is alive.
_CASCADES: dict[int, tuple[Element, _Cascade]] = {}


def _cascade_for(root: Element) -> _Cascade:
    """The cascade of this page, built on first use."""
    entry = _CASCADES.get(id(root))
    if entry is None or entry[0] is not root:
        if len(_CASCADES) > 8:
            _CASCADES.clear()
        entry = (root, _Cascade(root))
        _CASCADES[id(root)] = entry
    return entry[1]


# Registered rules — declaring them in a list makes ``--ignore`` cheap.

def check_media_alternatives(root: Element) -> list[Finding]:
    """
    Rules ``video-missing-captions``, ``audio-missing-transcript``,
    ``track-missing-srclang`` and ``media-missing-controls``.

    WCAG 1.2 (Time-based Media) is the one success-criterion family no other
    rule here touches, and it is the family that locks a Deaf or
    hard-of-hearing visitor out of a page entirely rather than merely making it
    awkward. A ``<video>`` with no caption track is not a degraded experience;
    it is no experience.

    What this can and cannot see: a static linter can tell that a caption track
    is *declared*, never that its text is correct or synchronised. It reports
    the absence, which is the failure it can prove.
    """
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag not in ("video", "audio"):
            continue

        # A media element handed to a script (no controls, no autoplay) is
        # usually decorative background; requiring captions on a silent
        # looping hero video would be noise. Sound is what triggers WCAG 1.2.
        decorative = (
            elem.tag == "video"
            and "muted" in elem.attrs
            and "controls" not in elem.attrs
        )

        tracks = [d for d in walk(elem) if d.tag == "track"]
        kinds = {t.attrs.get("kind", "subtitles").strip().lower() for t in tracks}

        if elem.tag == "video" and not decorative and not (kinds & {"captions", "subtitles"}):
            findings.append(Finding(
                rule="video-missing-captions",
                line=elem.line,
                message=(
                    '<video> has no <track kind="captions">. WCAG 1.2.2 (level A): '
                    "prerecorded video with audio needs captions."
                ),
            ))

        if elem.tag == "audio" and not accessible_name(elem) and not tracks:
            findings.append(Finding(
                rule="audio-missing-transcript",
                line=elem.line,
                message=(
                    "<audio> has no caption track and no accessible name pointing at a "
                    "transcript. WCAG 1.2.1 (level A): prerecorded audio needs a text alternative."
                ),
            ))

        # ``controls`` is not itself a WCAG criterion, but a media element with
        # neither controls nor a scripted alternative cannot be operated from
        # the keyboard at all, which is 2.1.1.
        if "controls" not in elem.attrs and not decorative:
            findings.append(Finding(
                rule="media-missing-controls",
                line=elem.line,
                message=(
                    f"<{elem.tag}> has no controls attribute: nothing to operate from the "
                    "keyboard. WCAG 2.1.1 (level A)."
                ),
            ))

        for track in tracks:
            if not track.attrs.get("srclang", "").strip():
                findings.append(Finding(
                    rule="track-missing-srclang",
                    line=track.line,
                    message=(
                        "<track> missing srclang: assistive technology cannot tell which "
                        "language the captions are in."
                    ),
                ))
    return findings


def check_media_autoplay(root: Element) -> list[Finding]:
    """
    Rule ``media-autoplay-sound``.

    Audio that starts by itself and runs past three seconds masks a screen
    reader's own speech — the user cannot hear the tool they navigate with,
    and on many pages cannot find the control to stop it either. WCAG 1.4.2
    (level A) requires a pause or stop mechanism; ``muted`` satisfies it
    outright, so only unmuted autoplay is reported.
    """
    findings: list[Finding] = []
    for elem in walk(root):
        if elem.tag not in ("video", "audio"):
            continue
        if "autoplay" in elem.attrs and "muted" not in elem.attrs:
            findings.append(Finding(
                rule="media-autoplay-sound",
                line=elem.line,
                message=(
                    f"<{elem.tag} autoplay> without muted: sound starts on its own and "
                    "masks a screen reader. WCAG 1.4.2 (level A) — add muted, or a stop control."
                ),
            ))
    return findings


ALL_RULES: dict[str, Callable[..., Any]] = {
    "html-missing-lang": check_html_lang,
    "img-missing-alt": check_img,
    "img-redundant-aria": check_img,
    "a-missing-href": check_links,
    "a-empty": check_links,
    "button-empty": check_buttons,
    "div-onclick": check_divspan_onclick,
    "input-missing-label": check_input_label,
    "dialog-missing-close": check_dialog_close,
    "tabindex-positive": check_tabindex_positive,
    "aria-hidden-interactive": check_aria_hidden_interactive,
    "heading-skip": check_heading_order,
    "color-only-state": check_color_only_state,
    "motion-no-reduce-guard": check_motion_reduce,
    "body-text-tracking-tight": check_body_text_tracking,
    # WCAG 1.2 — time-based media. Captions and transcripts are the one
    # family whose absence locks a visitor out rather than slowing them down.
    "video-missing-captions": check_media_alternatives,
    "audio-missing-transcript": check_media_alternatives,
    "track-missing-srclang": check_media_alternatives,
    "media-missing-controls": check_media_alternatives,
    "media-autoplay-sound": check_media_autoplay,
    # Reading comfort for dyslexic readers and other reading difficulties:
    # WCAG 1.4.8 (AAA) and the British Dyslexia Association style guide.
    "body-text-justified": check_reading_alignment,
    "body-text-centered-long": check_reading_alignment,
    "body-text-italic-long": check_reading_italic,
    "body-text-all-caps-long": check_reading_capitals,
    "body-text-leading-tight": check_reading_leading,
    "body-text-line-too-long": check_reading_line_length,
    "text-underline-not-link": check_reading_underline,
}


# ── Auto-fix machinery ────────────────────────────────────────────────────

#: One opening tag, up to its ``>`` or the end of the line. Quoted attribute
#: values are matched whole, so a ``>`` inside one does not end the tag.
_TAG_RE: re.Pattern[str] = re.compile(r"""<[a-zA-Z][\w:-]*(?:[^<>"']|"[^"]*"|'[^']*')*>?""")

#: The ``class`` attribute inside one tag, and not ``data-class``.
_CLASS_ATTR_RE: re.Pattern[str] = re.compile(r"""(?<![-\w])class=(["'])((?:(?!\1).)*)\1""")


def read_source(path: Path) -> str:
    """Read an HTML file so that :func:`write_source` gives its bytes back.

    ``newline=""`` keeps the line endings, and ``surrogateescape`` carries a
    byte that is not UTF-8 through as a placeholder. The fixers used to read
    with ``errors="ignore"`` and write back what was left: on a Latin-1 page
    every accented letter vanished, even when no fix applied, and a CRLF file
    came out LF. A read for the lint alone can drop such a byte; a read that
    will be written back cannot.
    """
    with path.open(encoding="utf-8", errors="surrogateescape", newline="") as handle:
        return handle.read()


def write_source(path: Path, text: str) -> None:
    """Write text obtained from :func:`read_source`, byte for byte."""
    with path.open("w", encoding="utf-8", errors="surrogateescape", newline="") as handle:
        handle.write(text)


def tags_on_line(line: str, offending: Callable[[Element], bool]) -> list[re.Match[str]]:
    """The opening tags on ``line`` that ``offending`` accepts, left to right.

    A finding carries a line and no column, and on a minified page one line
    holds many elements. The fixers used to edit the first attribute of the
    right name on the line, whichever element it belonged to, so a repair
    could strip the ``aria-hidden`` of the decorative icon beside the control
    it was meant for. Each tag is parsed by the parser the rules read, and
    ``offending`` is the rule's own test, so the two cannot disagree.
    """
    found: list[re.Match[str]] = []
    for match in _TAG_RE.finditer(line):
        source = match.group(0)
        builder = TreeBuilder()
        builder.feed(source if source.endswith(">") else f"{source}>")
        builder.close()
        if builder.root.children and offending(builder.root.children[0]):
            found.append(match)
    return found


def _edit_offending_tag(
    lines: list[str],
    finding: Finding,
    offending: Callable[[Element], bool],
    edit: Callable[[str], str],
) -> bool:
    """Apply ``edit`` to the first tag on the finding's line that offends."""
    idx: int = finding.line - 1
    if not (0 <= idx < len(lines)):
        return False
    tags = tags_on_line(lines[idx], offending)
    if not tags:
        return False
    match = tags[0]
    new_tag: str = edit(match.group(0))
    if new_tag == match.group(0):
        return False
    lines[idx] = lines[idx][: match.start()] + new_tag + lines[idx][match.end() :]
    return True


def _detect_html_lang(lines: list[str]) -> str | None:
    """Detect the document language from the HTML's own visible body text.

    Uses the shared :func:`_lang.extract_body_text` (HTML → visible text) and
    :func:`_lang.detect_text_language`. Returns a two-letter code, or ``None``
    when the language cannot be determined — ``langdetect`` absent, or too
    little text. **There is no default language**: the caller then leaves the
    finding unfixed rather than guessing.

    Parameters
    ----------
    lines : list of str
        The full HTML source, split into lines.

    Returns
    -------
    str or None
        Lower-case two-letter language code, or ``None`` if undetectable.
    """
    text: str = extract_body_text("\n".join(lines), "html")
    if len("".join(text.split())) < 20:
        return None
    # Empty fallback → ``detect_text_language`` returns "" when it cannot
    # detect (langdetect missing / low signal); map that to None (no default).
    code: str = detect_text_language(text, fallback="")
    return code or None


def _fix_html_missing_lang(lines: list[str], finding: Finding) -> bool:
    """Insert ``lang="<detected>"`` into the ``<html …>`` opening tag.

    The language is **detected from the document's own visible body text** —
    there is no default language. When it cannot be detected (``langdetect``
    absent, or too little text), the finding is left unfixed for a human
    rather than guessing.
    """
    idx: int = finding.line - 1
    if not (0 <= idx < len(lines)):
        return False
    line: str = lines[idx]
    # Only patch when the tag has no lang attr at all — re-running against a
    # fixed file is a no-op.
    if re.search(r"<html\b[^>]*\blang=", line, re.IGNORECASE):
        return False
    lang: str | None = _detect_html_lang(lines)
    if not lang:
        return False  # cannot detect the language → do not inject a default
    new_line: str = re.sub(
        r"<html\b", f'<html lang="{lang}"', line, count=1, flags=re.IGNORECASE,
    )
    if new_line == line:
        return False
    lines[idx] = new_line
    return True


def _fix_img_redundant_aria(lines: list[str], finding: Finding) -> bool:
    """Strip redundant ``role="presentation"`` / ``aria-hidden="true"`` from <img alt="">."""

    def edit(tag: str) -> str:
        tag = re.sub(r'\s+role=["\']presentation["\']', "", tag, count=1)
        return re.sub(r'\s+aria-hidden=["\']true["\']', "", tag, count=1)

    return _edit_offending_tag(lines, finding, _has_redundant_aria, edit)


def _fix_tabindex_positive(lines: list[str], finding: Finding) -> bool:
    """Demote ``tabindex="N>0"`` to ``tabindex="0"`` (preserves focusability)."""
    idx: int = finding.line - 1
    if not (0 <= idx < len(lines)):
        return False
    line: str = lines[idx]
    new_line: str = re.sub(
        r'tabindex=(["\'])(?:[1-9]\d*)\1', r'tabindex=\g<1>0\1',
        line, count=1,
    )
    if new_line == line:
        return False
    lines[idx] = new_line
    return True


def _fix_aria_hidden_interactive(lines: list[str], finding: Finding) -> bool:
    """Strip ``aria-hidden="true"`` from an interactive element."""

    def edit(tag: str) -> str:
        return re.sub(r'\s+aria-hidden=["\']true["\']', "", tag, count=1)

    return _edit_offending_tag(lines, finding, _hides_a_focusable_control, edit)


def _fix_motion_reduce_guard(lines: list[str], finding: Finding) -> bool:
    """Append a ``motion-reduce:`` guard to the offending element's class list."""

    def edit(tag: str) -> str:
        m = _CLASS_ATTR_RE.search(tag)
        if m is None:
            return tag
        new_classes: str = " ".join([*m.group(2).split(), "motion-reduce:transform-none"])
        return tag[: m.start(2)] + new_classes + tag[m.end(2) :]

    return _edit_offending_tag(lines, finding, _animates_unguarded, edit)


def _fix_body_text_tracking_tight(lines: list[str], finding: Finding) -> bool:
    """Strip ``tracking-tight``/``tracking-tighter`` from the offending element's class list."""

    def edit(tag: str) -> str:
        m = _CLASS_ATTR_RE.search(tag)
        if m is None:
            return tag
        remaining: list[str] = [
            c for c in m.group(2).split() if not _TIGHT_TRACKING_PAT.fullmatch(c)
        ]
        return tag[: m.start(2)] + " ".join(remaining) + tag[m.end(2) :]

    return _edit_offending_tag(lines, finding, _is_tight_body_text, edit)


#: Mapping of rule id → fixer. Only rules whose violations have a
#: single safe mechanical repair appear here. Empty links / empty
#: buttons / missing labels / missing headings / color-only state
#: are deliberately absent — those need a content decision the
#: linter cannot make for the user.
RULE_FIXERS: dict[str, Callable[..., Any]] = {
    "html-missing-lang": _fix_html_missing_lang,
    "img-redundant-aria": _fix_img_redundant_aria,
    "tabindex-positive": _fix_tabindex_positive,
    "aria-hidden-interactive": _fix_aria_hidden_interactive,
    "motion-no-reduce-guard": _fix_motion_reduce_guard,
    "body-text-tracking-tight": _fix_body_text_tracking_tight,
}


#: Maximum fix→lint→fix passes per file. None of the current fixers
#: introduces new findings (unlike Jakob in audit_laws_of_ux); a
#: single pass is enough. The cap is here for symmetry and safety.
MAX_FIX_ITERATIONS: int = 3


def fix_file(
    path: Path, ignored: set[str], *, dry_run: bool = False
) -> tuple[int, int, list[Finding]]:
    """
    Apply mechanical accessibility fixes to one HTML file in place.

    Idempotent: a second invocation against a fixed file applies
    zero edits. Iterates the lint→fix loop up to
    :data:`MAX_FIX_ITERATIONS` times — no current fixer introduces
    new findings, but the cap leaves headroom for future additions.

    Parameters
    ----------
    path : Path
        File to repair.
    ignored : set of str
        Rule ids to suppress (passed through to :func:`lint_file`).
    dry_run : bool, default False
        If ``True``, never write to disk — just compute and return
        the would-be counts.

    Returns
    -------
    (int, int, list of Finding)
        ``(applied, skipped, remaining)`` — number of edits that
        landed, count of findings with no fixer, and the residual
        findings after the final write.
    """
    raw: str = read_source(path)
    # ``split``, not ``splitlines``: the latter also breaks on a form feed or a
    # U+2028, which the parser's line numbers do not count, and the join below
    # would turn them into newlines.
    bare_lines: list[str] = raw.split("\n")
    written: str = raw
    applied: int = 0
    skipped: int = 0
    skipped_seen: bool = False

    if dry_run:
        findings: list[Finding] = lint_file(path, ignored)
        for f in findings:
            fixer = RULE_FIXERS.get(f.rule)
            if fixer is None:
                skipped += 1
                continue
            shadow: list[str] = bare_lines[:]
            if fixer(shadow, f):
                applied += 1
        return applied, skipped, findings

    def write_if_changed() -> None:
        """Write the working lines back, and leave an unchanged file untouched."""
        nonlocal written
        new_text: str = "\n".join(bare_lines)
        if new_text != written:
            write_source(path, new_text)
            written = new_text

    for _ in range(MAX_FIX_ITERATIONS):
        write_if_changed()
        findings = lint_file(path, ignored)
        round_applied: int = 0
        round_skipped: int = 0
        for f in findings:
            fixer = RULE_FIXERS.get(f.rule)
            if fixer is None:
                round_skipped += 1
                continue
            if fixer(bare_lines, f):
                round_applied += 1
        applied += round_applied
        if not skipped_seen:
            skipped = round_skipped
            skipped_seen = True
        if round_applied == 0:
            break
    write_if_changed()
    remaining: list[Finding] = lint_file(path, ignored)
    return applied, skipped, remaining


# ── Orchestration ────────────────────────────────────────────────────────

def lint_html(html: str, ignored: set[str] | None = None) -> list[Finding]:
    """
    Run every enabled rule against a string of HTML.

    The real implementation; :func:`lint_file` reads a file and calls this.
    Split out because the HTTP and MCP surfaces lint markup that never
    touches disk — a caller posting a template fragment should not have to
    invent a temporary file, and a second copy of the rule loop would be
    free to drift from this one.

    Parameters
    ----------
    html : str
        HTML source. A fragment is fine; the parser does not require a
        complete document.
    ignored : set of str, optional
        Rule identifiers to suppress. ``None`` means suppress nothing.

    Returns
    -------
    list of Finding
        All findings from the enabled rules, ordered by line then rule.

    Examples
    --------
    >>> [f.rule for f in lint_html('<img src="a.png">')]
    ['img-missing-alt']
    """
    ignored = ignored or set()
    parser = TreeBuilder()
    parser.feed(html)
    parser.close()

    findings: list[Finding] = []
    # Some rule functions emit two rule ids (e.g. ``check_img`` for missing
    # alt and redundant aria). Run each distinct rule function once and
    # then filter findings by the ignored set.
    seen: set[int] = set()
    for fn in {ALL_RULES[r] for r in ALL_RULES if r not in ignored}:
        if id(fn) in seen:
            continue
        seen.add(id(fn))
        for f in fn(parser.root):
            if f.rule in ignored:
                continue
            findings.append(f)

    # Stable order: by line, then by rule.
    findings.sort(key=lambda x: (x.line, x.rule))
    return findings


def lint_file(path: Path, ignored: set[str] | None = None) -> list[Finding]:
    """
    Run every enabled rule against one HTML file.

    Thin wrapper over :func:`lint_html`: reads the file, lints the text.

    ``ignored`` defaults to suppressing nothing, which is what the command
    line does when ``--ignore`` is absent. It had no default while
    :func:`lint_html`, the function this one wraps, did -- so the file entry
    point, the one a caller reaches for first, was strictly harder to call
    than the string entry point behind it, and demanded an opinion about rule
    suppression from a caller who has none.

    Parameters
    ----------
    path : Path
        HTML file to lint.
    ignored : set of str, optional
        Rule identifiers to suppress. Default: suppress nothing.

    Returns
    -------
    list of Finding
        All findings from the enabled rules, deduplicated by (rule, line).
    """
    return lint_html(path.read_text(encoding="utf-8", errors="ignore"), ignored)


def collect_targets(target: Path) -> list[Path]:
    """
    Resolve ``target`` to a list of ``.html`` files to lint.

    Parameters
    ----------
    target : Path
        File or directory.

    Returns
    -------
    list of Path
        Every ``.html`` file at or under ``target``.
    """
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.html"))


def _build_cli() -> Any:
    """Build the click command. click is imported here, not at module top.

    ``from lint_a11y import lint_html`` is how the downloadable toolbox kit on
    sprezzature.ai uses this module, with nothing installed: the rules need
    only the standard library, and only the command line needs click.
    """
    import click
    from _click import sprezzature_command

    @sprezzature_command(
        name="sprezzature-accessibility-lint",
        help="W3C/WAI accessibility linter for HTML emitted by the sprezzature skill. "
        "27 rules, exit 1 on any finding. Pre-commit gate — pair with axe-core "
        "or Pa11y for runtime DOM audits.",
        # ``\b`` keeps the examples one per line: click rewraps an epilog into a
        # single paragraph otherwise.
        epilog="\b\nExamples:\n"
        "  sprezzature-accessibility-lint public/index.html\n"
        "  sprezzature-accessibility-lint --format json public/\n"
        "  sprezzature-accessibility-lint --ignore img-missing-alt,a-missing-href dist/\n",
    )
    # ``exists=True``: a path with a typo in it used to print "No HTML files
    # found" and exit 0, so a CI step pointing at the wrong folder stayed green.
    @click.argument("target", type=click.Path(exists=True, path_type=Path))
    @click.option(
        "--format",
        "format_",
        type=click.Choice(["text", "json"]),
        default="text",
        help="Output format. Default: text.",
    )
    @click.option(
        "--ignore",
        default="",
        help="Comma-separated list of rule ids to skip.",
    )
    @click.option(
        "--fix",
        is_flag=True,
        help=(
            "Apply safe mechanical fixes in place: add lang to <html>, "
            "strip redundant role/aria-hidden from decorative <img alt=''>, "
            "demote tabindex>0 to 0, strip aria-hidden from interactive "
            "elements, append motion-reduce:transform-none to animated "
            "elements, strip tracking-tight/tighter from body text. "
            "Rules without a fixer (empty button, missing "
            "label, heading skip, etc.) are passed through honestly. "
            "Idempotent."
        ),
    )
    @click.option(
        "--fix-alt",
        "fix_alt",
        is_flag=True,
        help=(
            "Draft the missing alt text and write it in, using the image AND "
            "the surrounding text of the very page being fixed. Separate from "
            "--fix on purpose: --fix is mechanical, offline and idempotent, "
            "while this calls a local vision model, takes seconds per image, "
            "and writes prose a human should read before committing. Needs "
            "Ollama and qwen3-vl:8b: sprezzature-accessibility-install-alt."
        ),
    )
    @click.option(
        "--alt-lang",
        "alt_lang",
        default=None,
        metavar="TAG",
        help=(
            "BCP-47 base tag for drafted alt text. When omitted: the page's "
            "<html lang>, then detection on the page text, then the "
            "environment locale. A French page should not get English alt "
            "because the machine's locale is English."
        ),
    )
    @click.option(
        "--dry-run",
        "dry_run",
        is_flag=True,
        help=(
            "With --fix, print what would change without touching the "
            "files. Implies --fix when used alone. Always exits 0."
        ),
    )
    def _cli(
        target: Path,
        format_: str,
        ignore: str,
        fix: bool,
        fix_alt: bool,
        alt_lang: str | None,
        dry_run: bool,
    ) -> int:
        """Run the lint, the fixers or the drafter over *target*."""
        # One namespace so the body below reads the flags as it did when argparse
        # built them; click hands them over as keyword arguments instead.
        args = SimpleNamespace(
            target=target,
            format=format_,
            ignore=ignore,
            fix=fix,
            fix_alt=fix_alt,
            alt_lang=alt_lang,
            dry_run=dry_run,
        )

        ignored: set[str] = {r.strip() for r in args.ignore.split(",") if r.strip()}
        paths = collect_targets(args.target)
        if not paths:
            sys.stderr.write(f"No HTML files found under {args.target}\n")
            return 0

        # ── Drafting pass ─────────────────────────────────────────────────
        # Runs before the mechanical pass so the alt it writes is visible to the
        # lint that follows: an image that now has alt="" would be reported as a
        # decorative one with a redundant role, and --fix should get to clean
        # that up in the same invocation.
        if args.fix_alt:
            from fill_alt import fill_missing_alt

            drafted = 0
            for path in paths:
                drafts, unreachable = fill_missing_alt(
                    path, ignored, lang=args.alt_lang, dry_run=args.dry_run
                )
                drafted += len(drafts)
                for draft in drafts:
                    sys.stderr.write(
                        f"{path}:{draft.line}: drafted from {draft.src} "
                        f"with {draft.context_chars} chars of page context\n"
                    )
                for finding in unreachable:
                    sys.stderr.write(
                        f"{path}:{finding.line}: left alone — the image is remote, "
                        f"missing, or the tag spans lines\n"
                    )
            if drafted:
                sys.stderr.write(
                    f"{drafted} draft(s) written. They are drafts: a model cannot "
                    f"know that the photograph on the About page is the founder. "
                    f"Read them before committing.\n"
                )

        # ── Fix mode ──────────────────────────────────────────────────────
        # ``--dry-run`` alone implies ``--fix`` (preview only). When the
        # user runs ``--fix``, we apply the safe mechanical fixes in place,
        # then emit the residual findings in the requested format so a CI
        # pipeline can still gate on them.
        if args.fix or args.dry_run or args.fix_alt:
            total_applied: int = 0
            total_skipped: int = 0
            total_remaining: list[Finding] = []
            for path in paths:
                applied, skipped, remaining = fix_file(
                    path, ignored, dry_run=args.dry_run
                )
                total_applied += applied
                total_skipped += skipped
                total_remaining.extend(remaining)
                verb: str = "would apply" if args.dry_run else "applied"
                sys.stderr.write(
                    f"{path}: {verb} {applied} fix(es); "
                    f"{skipped} unfixable finding(s); "
                    f"{len(remaining)} remaining.\n"
                )
            if args.format == "json":
                json.dump(
                    {
                        "applied": total_applied,
                        "skipped": total_skipped,
                        "findings_total": len(total_remaining),
                        "findings": [
                            {"rule": f.rule, "line": f.line, "message": f.message}
                            for f in total_remaining
                        ],
                    },
                    sys.stdout, indent=2, ensure_ascii=False,
                )
                sys.stdout.write("\n")
            else:
                if total_remaining:
                    print(
                        f"{len(total_remaining)} remaining finding(s) after "
                        f"{'preview' if args.dry_run else 'fix'} pass."
                    )
                else:
                    print("0 findings remaining.")
            # Dry-run is a preview, not a verdict — always exit 0.
            if args.dry_run:
                return 0
            return 0 if not total_remaining else 1

        # ── Audit-only mode ───────────────────────────────────────────────
        total: int = 0
        failing_files: int = 0
        report: list[dict] = []
        for path in paths:
            findings = lint_file(path, ignored)
            if not findings:
                continue
            total += len(findings)
            failing_files += 1
            if args.format == "text":
                print(f"{path}:")
                for f in findings:
                    print(f"  L{f.line:>4}  [{f.rule}] {f.message}")
            # ``report`` is populated in both formats so the JSON output has the
            # same coverage as the text output.
            report.append({
                "file": str(path),
                "findings": [
                    {"rule": f.rule, "line": f.line, "message": f.message}
                    for f in findings
                ],
            })

        if args.format == "json":
            json.dump({"findings_total": total, "files": report},
                      sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
        else:
            print()
            if total == 0:
                print("0 findings.")
            else:
                print(f"{total} finding(s) across {failing_files} file(s).")

        return 0 if total == 0 else 1

    return _cli


def main(argv: list[str] | None = None) -> int:
    """
    CLI entry point.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector excluding ``argv[0]``. ``None`` reads ``sys.argv``.

    Returns
    -------
    int
        ``0`` on no findings, ``1`` on any finding, ``2`` on a usage error.
    """
    from _click import run_command

    return run_command(_build_cli(), argv)


if __name__ == "__main__":
    sys.exit(main())

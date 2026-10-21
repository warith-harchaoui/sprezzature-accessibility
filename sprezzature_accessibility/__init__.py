"""
sprezzature-accessibility — static HTML accessibility linter.

Two halves of one job — **audit** what a page gets wrong about
accessibility, and **make** the content it is missing.

The audit half: twenty rules from WCAG (Web Content Accessibility Guidelines) and
WAI-ARIA (the W3C's accessible-widget attribute vocabulary), each
decidable by reading the HTML source alone, with no browser involved:
missing alt text, unlabelled inputs, empty buttons, onclick divs,
missing dialog close, lang attribute, heading order, color-only state,
motion-reduce guards, and five checks on time-based media (captions,
track language, media controls). Six of the twenty also ship a
mechanical fixer. Stdlib only (Python 3.10+). Pairs with axe-core /
Pa11y, which check the page after a browser has rendered it (the
"runtime DOM"), for the failures that only show up there.

The make half, behind the ``[alt]`` extra: draft W3C-conformant alt text
for an image with a local vision model, following the WAI image-purpose
decision tree. It arrived when ``sprezzature-vision`` was folded in here
— auditing a page for missing alt text and writing the alt text are two
halves of one job, and splitting them across two packages meant the
audit could only ever say what was wrong.
"""

__version__ = "1.2.1"
__author__ = "Warith HARCHAOUI"
__email__ = "warithmetics@deraison.ai"
__license__ = "BSD-3-Clause"

from typing import Any  # noqa: E402

from sprezzature_accessibility_scripts.lint_a11y import (  # noqa: E402
    Finding,
    fix_file,
    lint_file,
)

#: Image purposes from the W3C alt-text decision tree, in the order the tree
#: asks about them. Exported because every surface needs the same list: the
#: command lines validate against it, the API publishes it as an enum, and the
#: MCP tool schema is derived from the API.
KINDS: tuple[str, ...] = (
    "informative",
    "decorative",
    "functional",
    "text",
    "complex",
    "group",
)

#: Names served lazily from the drafting half. They live behind the ``[alt]``
#: extra, and importing them eagerly would drag click and an LLM helper into
#: ``import sprezzature_accessibility`` — breaking the promise that makes the
#: lint worth reaching for: zero dependencies, milliseconds, no browser, runs
#: in any pre-commit hook.
_ALT_EXPORTS = {
    "DEFAULT_BASE", "MAX_CHARS", "describe", "describe_long", "detect_lang",
    "compose_vocabulary_hint", "load_image_bytes", "long_prompt_for",
    "maybe_resize", "pick_default_model", "post_process", "prompt_for",
    "surrounding_text",
}


def __getattr__(name: str) -> Any:
    """Resolve a drafting export on first use, per PEP 562.

    A caller who only lints never triggers this, and so never needs the extra.
    A caller who asks for ``describe`` without the extra installed gets a
    sentence naming the install command rather than a bare ImportError about
    a module they have never heard of.
    """
    if name not in _ALT_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        if name == "surrounding_text":
            from sprezzature_accessibility_scripts._vocab import surrounding_text
            return surrounding_text
        import sprezzature_accessibility_scripts.alt_from_ollama as engine
    except ImportError as exc:
        raise ImportError(
            f"`{name}` belongs to the alt-text drafting half of this package, "
            f"which is an optional extra so the lint stays dependency-free. "
            f"Install it with: pip install 'sprezzature-accessibility[alt]'"
        ) from exc
    return getattr(engine, name)


__all__ = [
    # audit
    "Finding",
    "fix_file",
    "lint_file",
    # make
    "KINDS",
    *sorted(_ALT_EXPORTS),
    "__version__",
]

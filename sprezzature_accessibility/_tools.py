#!/usr/bin/env python3
"""
The catalogue of tools this package ships, and the one sentence said about a
missing extra.

Lifted out of the command line on 2026-10-25, when the argparse front door was
removed and click became the only one. It lives here rather than in ``cli`` so
the catalogue owes nothing to whichever parser reads it — the previous
arrangement had the click module importing ``TOOLS`` from the argparse module,
which is why neither could be deleted without the other.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

#: ``name -> (module, extra, summary)``, the single catalogue both front doors
#: read. The summary is what ``--help`` prints, so a tool cannot be listed and
#: unreachable, or reachable and undocumented.
#:
#: The module is a **full dotted path** rather than a bare name, because these
#: four do not all live in one place: the audit half is in the scripts
#: package, the drafting half's command line is in this one. A table that
#: assumed a single prefix would have quietly excluded ``alt``.
#:
#: ``extra`` is empty for the two halves that need nothing. That is the shape
#: of this package and not an accident: the lint is standard-library only,
#: milliseconds, no browser — which is what makes it worth putting in a
#: pre-commit hook — and everything that needs a model sits behind ``[alt]``.
TOOLS: dict[str, tuple[str, str, str]] = {
    "lint": (
        "sprezzature_accessibility_scripts.lint_a11y",
        "",
        "Report what a page gets wrong about accessibility, from the HTML "
        "source alone: missing alt text, unlabelled inputs, empty buttons, "
        "onclick divs, heading order, motion guards. Standard library only.",
    ),
    "text-spacing": (
        "sprezzature_accessibility_scripts.text_spacing_preset",
        "",
        "Emit the CSS for an opt-in comfortable-reading toggle — line height, "
        "letter spacing, word spacing — at the WCAG 1.4.12 values.",
    ),
    "alt": (
        "sprezzature_accessibility.alt_cli",
        "alt",
        "Draft W3C-conformant alt text for an image with a local vision "
        "model, following the WAI image-purpose decision tree.",
    ),
    "install-alt": (
        "sprezzature_accessibility_scripts.install_alt_ai",
        "alt",
        "Install and warm the local Ollama vision model the drafting half "
        "needs, so the first `alt` call is not also a download.",
    ),
}


def missing_extra_message(tool: str, extra: str, exc: Exception) -> str:
    """What to say when a tool's dependency is not installed.

    Shared with the click twin so the two front doors cannot drift into
    saying different things about the same missing package.
    """
    if extra:
        return (
            f"{tool}: its dependencies are an optional extra, so a bare "
            f"install stays small. Add them with:\n"
            f"    pip install 'sprezzature-accessibility[{extra}]'\n"
            f"  ({exc})\n"
        )
    return (
        f"{tool}: needs nothing optional, so this is not a missing extra — "
        f"something else failed to import.\n  ({exc})\n"
    )

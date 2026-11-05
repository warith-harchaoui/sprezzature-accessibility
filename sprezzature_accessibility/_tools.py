#!/usr/bin/env python3
"""
The catalogue of tools this package ships, and the one sentence said when one
of them fails to import.

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

#: ``name -> (module, summary)``, the single catalogue both front doors
#: read. The summary is what ``--help`` prints, so a tool cannot be listed and
#: unreachable, or reachable and undocumented.
#:
#: The module is a **full dotted path** rather than a bare name, because these
#: four do not all live in one place: the audit half is in the scripts
#: package, the drafting half's command line is in this one. A table that
#: assumed a single prefix would have quietly excluded ``alt``.
#:
#: There was a middle field, the extra a tool needed, until 2026-11-05. It had
#: named ``""`` for all four since 2026-11-01, when every tool moved into the
#: base install, and its only reader was a branch printing
#: ``pip install 'sprezzature-accessibility[...]'`` that could no longer run.
TOOLS: dict[str, tuple[str, str]] = {
    "lint": (
        "sprezzature_accessibility_scripts.lint_a11y",
        "Report what a page gets wrong about accessibility, from the HTML "
        "source alone: missing alt text, unlabelled inputs, empty buttons, "
        "onclick divs, heading order, motion guards. Standard library only.",
    ),
    "text-spacing": (
        "sprezzature_accessibility_scripts.text_spacing_preset",
        "Emit the CSS for an opt-in comfortable-reading toggle — line height, "
        "letter spacing, word spacing — at the WCAG 1.4.12 values.",
    ),
    "alt": (
        "sprezzature_accessibility.alt_cli",
        "Draft W3C-conformant alt text for an image with a local vision "
        "model, following the WAI image-purpose decision tree.",
    ),
    "install-alt": (
        "sprezzature_accessibility_scripts.install_alt_ai",
        "Install and warm the local Ollama vision model the drafting half "
        "needs, so the first `alt` call is not also a download.",
    ),
}


def broken_install_message(tool: str, exc: Exception) -> str:
    """What to say when a tool fails to import.

    Every tool is in the base install, so a failed import is a broken install
    (a ``--no-deps`` one, or a half-upgraded one), and the repair is the
    install line itself. Until 2026-11-05 this was ``missing_extra_message``
    and had a second branch naming an extra; no tool had one to name.
    """
    return (
        f"{tool}: everything it needs is in the base install, so this is not "
        f"a missing extra — something failed to import on a complete install. "
        f"Reinstall with:\n"
        f"    pip install sprezzature-accessibility\n"
        f"  ({exc})\n"
    )

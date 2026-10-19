"""
The argparse command line — ``make-a11y``.

This package shipped four tools and no way to see them together: each had its
own console script, and the suite's own ``SKILL.md`` told an agent the package
was "invoked as ``sprezzature-accessibility …``" — a command nothing
installed. A guard in the monorepo caught the gap; this module and its click
twin close it.

Every per-tool command stays exactly where it was. Nothing here replaces
``sprezzature-accessibility-lint``; it gives the four a catalogue.

The twin :mod:`sprezzature_accessibility.cli_click` reads the same
:data:`TOOLS` table and shares :func:`_missing_extra_message`, so a tool
cannot appear in one front door and be missing from the other, nor be
explained differently by each.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
import importlib
import sys

from sprezzature_accessibility_scripts._argparse import make_parser

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


def build_parser() -> argparse.ArgumentParser:
    """The parser, built separately so a test can read it without running it."""
    width = max(len(name) for name in TOOLS)
    catalogue = "\n".join(
        f"  {name:<{width}}  {summary}" for name, (_, _, summary) in TOOLS.items()
    )
    parser = make_parser(
        prog="make-a11y",
        description=(
            "Everything this package does with a page: audit what it gets "
            "wrong, and draft the content it is missing. One front door over "
            "the four tools it ships; each is also its own command, which is "
            "what a script should call."
        ),
        epilog=(
            f"Tools:\n{catalogue}\n"
            "\n"
            "Examples:\n"
            "  make-a11y lint site/\n"
            "  make-a11y lint site/ --fix\n"
            "  make-a11y text-spacing > spacing.css\n"
            "  make-a11y alt photo.jpg --kind informative\n"
            "\n"
            "Every argument after the tool name belongs to that tool; run\n"
            "`make-a11y <tool> --help` to see them.\n"
        ),
    )
    parser.add_argument(
        "tool",
        choices=sorted(TOOLS),
        help="Which tool to run. See the list below.",
    )
    # Everything after the tool name belongs to the tool, including flags this
    # parser also defines. Without REMAINDER, `make-a11y lint --help` would
    # print *this* help rather than the lint's, which is the opposite of what
    # the reader asked for.
    parser.add_argument(
        "rest",
        nargs=argparse.REMAINDER,
        help="Arguments passed through to the tool.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Dispatch to one of the four tools.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector without ``argv[0]``. Reads ``sys.argv`` when ``None``.

    Returns
    -------
    int
        Whatever the dispatched tool returns.
    """
    args = build_parser().parse_args(argv)
    module_name, extra, _ = TOOLS[args.tool]
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:  # pragma: no cover - dependency guard
        sys.stderr.write(_missing_extra_message(args.tool, extra, exc))
        return 2

    # The tools read sys.argv themselves — they were commands before they were
    # sub-commands, and they still are. Handing them a rewritten argv is what
    # lets both be true.
    saved = sys.argv
    try:
        sys.argv = [f"make-a11y {args.tool}", *args.rest]
        return int(module.main() or 0)
    finally:
        sys.argv = saved


def _missing_extra_message(tool: str, extra: str, exc: Exception) -> str:
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


if __name__ == "__main__":
    sys.exit(main())

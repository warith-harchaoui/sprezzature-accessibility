"""
The argparse command line — ``make-alt``.

Two parsers, one body. This module reads the flags with ``argparse``; the
click command in ``sprezzature_accessibility_scripts.alt_from_ollama`` reads the same
flags with ``click``; both then call the same :func:`run`, so they can differ
in how ``--kind`` is spelled and cannot differ in what ``--kind`` does.

Why both at all: ``argparse`` is in the standard library, so this command
works in a container with nothing else installed and in any environment where
adding a dependency is someone else's decision. ``click`` carries the richer
shapes — ``Choice`` validation, path types — without hand-rolling them. The
house contract (``SURFACES.md`` in the monorepo) asks for both wherever there
is a command line, and the reason is this file: a surface that only exists in
one flavour is a surface someone cannot reach.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sprezzature_accessibility_scripts._argparse import make_parser
from sprezzature_accessibility_scripts.alt_from_ollama import run

from . import KINDS


def build_parser() -> argparse.ArgumentParser:
    """The parser, built separately so a test can read it without running it."""
    parser = make_parser(
        prog="make-alt",
        description=(
            "Draft W3C-conformant alt text for an image with a local vision "
            "model. Follows the WAI image-purpose decision tree "
            "(informative / decorative / functional / text / complex / "
            "group). No image leaves the machine."
        ),
        epilog=(
            "Examples:\n"
            "  make-alt --kind informative photo.jpg\n"
            "  make-alt --kind functional "
            "--context 'Submit form' icon.png\n"
            "  make-alt --kind complex --in docs/chart.md "
            "chart.png\n"
            "\n"
            "What comes back is a draft. A model cannot know that the "
            "photograph on the About page is the founder, or that the chart "
            "matters for its outlier rather than its trend. Read it before "
            "committing it.\n"
        ),
    )
    parser.add_argument("src", help="Path or URL to the image.")
    parser.add_argument(
        "--kind",
        choices=KINDS,
        default="informative",
        help="Image purpose per the W3C decision tree (default: informative).",
    )
    parser.add_argument(
        "-l", "--lang",
        default=None,
        help="BCP-47 base tag (en, fr, es, de, …). Detected when omitted.",
    )
    parser.add_argument(
        "-c", "--context",
        default="",
        help=(
            "Page-context hint. For --kind functional, name the action or "
            "destination."
        ),
    )
    parser.add_argument(
        "--resize",
        type=int,
        default=1024,
        metavar="N",
        help="Downscale the long edge to N px before sending (default: 1024; "
             "0 disables).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass the on-disk cache for this run.",
    )
    parser.add_argument(
        "--longdesc",
        action="store_true",
        help=(
            "ALSO write a long description to <src>.longdesc.md. Only "
            "meaningful with --kind complex or group."
        ),
    )
    parser.add_argument(
        "--in",
        dest="in_doc",
        type=Path,
        metavar="DOC",
        default=None,
        help=(
            "Document the image is embedded in. The text around every "
            "reference to it is used as context and as a vocabulary source. "
            "Highest signal available."
        ),
    )
    parser.add_argument(
        "--vocab",
        type=Path,
        metavar="FILE",
        default=None,
        help="Glossary file; one term per line; '#' starts a comment.",
    )
    parser.add_argument(
        "--vocab-from",
        dest="vocab_from",
        type=Path,
        metavar="PATH",
        default=None,
        help="File or directory mined for proper nouns and identifiers.",
    )
    parser.add_argument(
        "--auto-project",
        dest="auto_project",
        action="store_true",
        help=(
            "Walk upward from the image to the project root and collect "
            "vocabulary from the whole tree."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Entry point for ``make-alt``.

    Parameters
    ----------
    argv : list of str or None, optional
        Argument vector without ``argv[0]``. Reads ``sys.argv`` when ``None``.

    Returns
    -------
    int
        ``0`` on success, ``2`` when the local model cannot be reached.
    """
    args = build_parser().parse_args(argv)
    return run(
        args.src,
        kind=args.kind,
        lang=args.lang,
        context=args.context,
        resize=args.resize,
        no_cache=args.no_cache,
        longdesc=args.longdesc,
        in_doc=args.in_doc,
        vocab=args.vocab,
        vocab_from=args.vocab_from,
        auto_project=args.auto_project,
    )


if __name__ == "__main__":
    sys.exit(main())

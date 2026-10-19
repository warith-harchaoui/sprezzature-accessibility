"""
The click command line — ``sprezzature-accessibility``.

The twin of ``sprezzature_accessibility.cli``: same options, same engine, a different
parser. Both call :func:`sprezzature_accessibility_scripts.alt_from_ollama.run`, so
they cannot disagree about what a flag does.

Why this lives here and not beside the engine
---------------------------------------------
It used to sit inside ``alt_from_ollama.py``, which the package's
``__init__`` imports. That made ``import sprezzature_accessibility`` depend on click
— a command-line framework pulled in by a caller who only wanted to describe
an image from their own code. Worse, click was declared nowhere in
``pyproject.toml``, so a clean ``pip install sprezzature-accessibility-alt`` produced a
package whose library *and* whose main command both failed on the first
import. Keeping the parser out of the engine module is what makes the library
surface honest.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path

# Guarded, like every other Click front door in this suite. Click is an extra
# here — the argparse twin needs nothing, which is the point of shipping both
# — so a bare `pip install` leaves this command on PATH and unable to start.
# Unguarded, what it printed was `ModuleNotFoundError: No module named
# 'click'`: a traceback about a package the reader never asked for, for a
# command their own install had just created.
try:
    import click
except ImportError:  # pragma: no cover - exercised by a bare install
    def main(argv: list[str] | None = None) -> int:
        """Say which extra installs this command, and exit non-zero.

        The signature matches the real ``main`` exactly — same parameter,
        same return type. Two conditional definitions that disagree are a
        type error, and more to the point they are a trap: a caller who
        imports ``main`` and passes an argv would get a TypeError on the
        machine where the extra is missing and nowhere else.
        """
        del argv  # the message is the same whatever was asked for
        print(
            "sprezzature-accessibility-alt is built with Click, which this "
            "package installs with an extra:\n"
            "    pip install 'sprezzature-accessibility[alt]'\n"
            "The lint and the text-spacing commands need nothing.",
            file=sys.stderr,
        )
        return 1
else:
    from sprezzature_accessibility_scripts._click import (
        run_command,
        sprezzature_command,
    )
    from sprezzature_accessibility_scripts.alt_from_ollama import run


    @sprezzature_command(
        "sprezzature-accessibility-alt",
        help=(
            "Generate W3C-compliant alt text for an image via a local Ollama "
            "vision model. Matches the WAI image-purpose decision tree "
            "(informative / decorative / functional / text / complex / group)."
        ),
        epilog=(
            "Examples:\n"
            "  sprezzature-accessibility-alt --kind informative photo.jpg\n"
            "  sprezzature-accessibility-alt --kind functional --context 'Submit form' icon.png\n"
            "  sprezzature-accessibility-alt --kind complex --in docs/chart.md chart.png\n"
        ),
    )
    @click.argument("src")
    @click.option(
        "--kind",
        type=click.Choice(
            ["informative", "decorative", "functional", "text", "complex", "group"]
        ),
        default="informative",
        show_default=True,
        help="Image purpose per W3C decision tree.",
    )
    @click.option(
        "--lang", "-l",
        default=None,
        help="BCP-47 base tag (en, fr, es, de, …).",
    )
    @click.option(
        "--context", "-c",
        default="",
        help="Page-context hint. For --kind functional, name the action/destination.",
    )
    @click.option(
        "--resize",
        type=int,
        default=1024,
        show_default=True,
        help="Downscale long edge to N px before sending (Pillow). 0 disables.",
    )
    @click.option(
        "--no-cache",
        "no_cache",
        is_flag=True,
        default=False,
        help="Bypass the on-disk cache for this run.",
    )
    @click.option(
        "--longdesc",
        is_flag=True,
        default=False,
        help=(
            "ALSO generate a long description (for <figcaption> or "
            "aria-describedby). Writes it to <src>.longdesc.md beside the "
            "image. Only meaningful with --kind complex or group."
        ),
    )
    # Vocabulary biasing — same shape as captions_from_whisper.py.
    @click.option(
        "--in",
        "in_doc",
        type=click.Path(path_type=Path),
        metavar="DOC",
        default=None,
        help=(
            "Document the image is embedded in. The text around every "
            "reference to the image inside DOC is used both as --context "
            "and as a vocabulary source. Highest signal for alt text."
        ),
    )
    @click.option(
        "--vocab",
        type=click.Path(path_type=Path),
        default=None,
        help="Glossary file; one term per line; '#' starts a comment.",
    )
    @click.option(
        "--vocab-from",
        "vocab_from",
        type=click.Path(path_type=Path),
        default=None,
        help="File or directory whose text is mined for proper nouns and identifiers.",
    )
    @click.option(
        "--auto-project",
        "auto_project",
        is_flag=True,
        default=False,
        help=(
            "Walk upward from the source to find the project root, then "
            "collect vocabulary from the whole tree."
        ),
    )
    def _cli(
        src: str,
        kind: str,
        lang: str | None,
        context: str,
        resize: int,
        no_cache: bool,
        longdesc: bool,
        in_doc: Path | None,
        vocab: Path | None,
        vocab_from: Path | None,
        auto_project: bool,
    ) -> int:
        """Click wrapper. The work is in :func:`run`, which argparse calls too."""
        return run(
            src,
            kind=kind,
            lang=lang,
            context=context,
            resize=resize,
            no_cache=no_cache,
            longdesc=longdesc,
            in_doc=in_doc,
            vocab=vocab,
            vocab_from=vocab_from,
            auto_project=auto_project,
        )



    def main(argv: list[str] | None = None) -> int:
        """
        CLI entry point.

        Parameters
        ----------
        argv : list of str or None, optional
            Argument vector excluding ``argv[0]``. When ``None`` (default),
            Click reads from ``sys.argv``.

        Returns
        -------
        int
            Process exit code. ``0`` on success, ``2`` on infrastructure failure
            (Ollama unreachable / HTTP error or a usage error).
        """
        return run_command(_cli, argv)


    if __name__ == "__main__":
        sys.exit(main())

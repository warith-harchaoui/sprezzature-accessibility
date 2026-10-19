"""
The click command line — ``sprezzature-accessibility``.

The twin of :mod:`sprezzature_accessibility.cli`: same four tools, same
dispatch, the other parser. Both read the single ``TOOLS`` table and share the
one sentence said about a missing extra, so a tool cannot appear in one front
door and be missing from the other, nor be explained differently by each.

This command is also the one the suite's ``SKILL.md`` has been naming. Until
1.2.0 that sentence promised a command nothing installed, and an agent
following the contract found out at the shell.

Click is an extra (``[click]``, and ``[alt]`` already carries it), and the
import below is guarded. The lint half of this package has **no**
dependencies — standard library, milliseconds, no browser — which is what
makes it worth putting in a pre-commit hook. A twin that imported click at
module load would end that silently, because the failure arrives at the
console script rather than at the install.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import importlib
import sys

from sprezzature_accessibility.cli import TOOLS, _missing_extra_message

try:
    import click
except ImportError:  # pragma: no cover - exercised by a bare install

    def main(argv: list[str] | None = None) -> int:
        """Say which extra installs this command, and exit non-zero.

        The signature matches the real ``main`` exactly. Two conditional
        definitions that disagree are a trap: a caller who imports ``main``
        and passes an argv gets a TypeError on the machine where the extra is
        missing, and nowhere else.
        """
        del argv  # the message is the same whatever was asked for
        print(
            "sprezzature-accessibility is the click front door, and click is "
            "an optional extra here:\n"
            "    pip install 'sprezzature-accessibility[click]'\n"
            "The argparse front door, `make-a11y`, needs nothing — the lint "
            "half of this package has no dependencies at all, which is what "
            "makes it cheap enough for a pre-commit hook.",
            file=sys.stderr,
        )
        return 1
else:

    @click.group(
        context_settings={"help_option_names": ["-h", "--help"]},
        help=(
            "Audit what a page gets wrong about accessibility, and draft the "
            "content it is missing. Each tool below is also its own command "
            "(sprezzature-accessibility-lint and so on), which is what a "
            "script should call."
        ),
    )
    @click.version_option(package_name="sprezzature-accessibility")
    def main() -> None:  # type: ignore[misc]  # pragma: no cover - click dispatches
        """Front door over the four tools this package ships."""

    def _attach(name: str, module_name: str, extra: str, summary: str) -> None:
        """Register one tool as a click sub-command.

        Built in a loop rather than written out four times: the catalogue
        lives in one table, and a tool added there appears in both command
        lines without anybody remembering to add it twice.
        """

        @main.command(  # type: ignore[attr-defined]
            name,
            help=summary,
            context_settings={
                "ignore_unknown_options": True,
                "allow_extra_args": True,
            },
        )
        @click.argument("rest", nargs=-1, type=click.UNPROCESSED)
        def _run(
            rest: tuple[str, ...],
            _module: str = module_name,
            _name: str = name,
            _extra: str = extra,
        ) -> None:
            try:
                module = importlib.import_module(_module)
            except ImportError as exc:  # pragma: no cover - dependency guard
                raise SystemExit(
                    _missing_extra_message(_name, _extra, exc).rstrip()
                ) from exc

            # The tools read sys.argv themselves — they were commands before
            # they were sub-commands, and they still are.
            saved = sys.argv
            try:
                sys.argv = [f"sprezzature-accessibility {_name}", *rest]
                raise SystemExit(int(module.main() or 0))
            finally:
                sys.argv = saved

    for _tool, (_module_name, _extra, _summary) in TOOLS.items():
        _attach(_tool, _module_name, _extra, _summary)


if __name__ == "__main__":
    main()

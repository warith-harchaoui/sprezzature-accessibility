"""
``sprezzature-accessibility`` — the command line over this package's tools.

One front door. Until 2026-10-25 there were two, an argparse one and a click
one kept in step by sharing a table; the click module imported ``TOOLS`` from
the argparse module, so neither could be removed without the other and every
sub-command had to be written twice. The catalogue now lives in
:mod:`sprezzature_accessibility._tools`, and this is the only parser.

``make-a11y`` and ``sprezzature-accessibility`` both land here. The first name is kept because it is what the
skill, the README and years of notes tell people to type; they are two
spellings of one command, not two commands.

Each tool below is also its own console script, which is what a script or a
pre-commit hook should call. This front door is for a person who does not
remember the exact name.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import importlib
import sys

import click

from sprezzature_accessibility._skill import skill_command
from sprezzature_accessibility._tools import TOOLS, broken_install_message

#: Shown under the command list. Completion is click's, and worth saying out
#: loud: a front door with several tools is exactly where tab completion pays
#: off, and nobody discovers it by guessing.
_EPILOG = """\
Shell completion:

  \b
  eval "$(_SPREZZATURE_ACCESSIBILITY_COMPLETE=bash_source sprezzature-accessibility)"   # bash
  eval "$(_SPREZZATURE_ACCESSIBILITY_COMPLETE=zsh_source sprezzature-accessibility)"    # zsh

Run `sprezzature-accessibility tools` to see which tools can run on this
machine. Every tool is in the base install, so one marked unavailable means a
broken install, not a missing extra.
"""


@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
    epilog=_EPILOG,
    help=(
        "Audit what a page gets wrong about accessibility, and draft the "
        "content it is missing. Each tool below is also its own command "
        "(sprezzature-accessibility-lint and so on), which is what a "
        "script should call."
    ),
)
# ``-V`` as well as ``--version``: every per-tool command answers both, and
# the README promises ``-h`` and ``-V`` on every command. The group answered
# ``--version`` only, so ``sprezzature-accessibility -V`` was a usage error.
@click.version_option(None, "-V", "--version", package_name="sprezzature-accessibility")
def main() -> None:  # pragma: no cover - click dispatches
    """Front door over the four tools this package ships."""


@main.command(name="tools")
def list_tools() -> None:
    """
    List the tools, and say which ones can run here.

    The second half is the point: "installed" and "will run" are different
    questions on a broken install, and a reader should not have to discover
    the difference from a traceback.
    """
    width = max(len(name) for name in TOOLS)
    for name, (module_name, summary) in TOOLS.items():
        try:
            importlib.import_module(module_name)
            mark = "ready"
        except ImportError:
            mark = "unavailable"
        # First sentence, cut on ". " rather than "." so a version number in
        # it survives: "WCAG 1.4.12" was printed as "WCAG 1.".
        summary = summary.split(". ")[0].rstrip(".")
        click.echo(f"  {name:<{width}}  {mark:<14}  {summary}.")


def _attach(name: str, module_name: str, summary: str) -> None:
    """Register one tool as a click sub-command.

    Built in a loop rather than written out four times: the catalogue
    lives in one table, and a tool added there appears in both command
    lines without anybody remembering to add it twice.
    """

    @main.command(
        name,
        help=summary,
        context_settings={
            "ignore_unknown_options": True,
            "allow_extra_args": True,
            # --help belongs to the tool: with a help option of its own this
            # stub answered it, with one line and a REST argument.
            "help_option_names": [],
        },
    )
    @click.argument("rest", nargs=-1, type=click.UNPROCESSED)
    def _run(
        rest: tuple[str, ...],
        _module: str = module_name,
        _name: str = name,
    ) -> None:
        try:
            module = importlib.import_module(_module)
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise SystemExit(broken_install_message(_name, exc).rstrip()) from exc

        # The tools read sys.argv themselves — they were commands before
        # they were sub-commands, and they still are.
        saved = sys.argv
        try:
            sys.argv = [f"sprezzature-accessibility {_name}", *rest]
            raise SystemExit(int(module.main(list(rest)) or 0))
        finally:
            sys.argv = saved


for _tool, (_module_name, _summary) in TOOLS.items():
    _attach(_tool, _module_name, _summary)


# The skill this package ships, one sub-command away: `sprezzature-accessibility skill --install`.
main.add_command(skill_command)


if __name__ == "__main__":
    main()

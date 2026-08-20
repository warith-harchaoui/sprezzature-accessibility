"""
_argparse — shared argparse parser factory for a sprezzature-* skill's scripts.

``make_parser(prog, description, epilog=None)`` returns an
``ArgumentParser`` pre-configured the way every script in this skill
expects:

- ``prog`` set explicitly so ``--help`` shows a clean name (no path).
- ``RawDescriptionHelpFormatter`` so multi-line descriptions and the
  optional ``epilog`` are not reflowed.
- A standard ``-V`` / ``--version`` option.

Duplicated on purpose across every sprezzature-* skill (each skill's
``scripts/_argparse.py`` is its own copy, not an import from a shared
package), so that every skill stays installable and usable on its own
without depending on another skill's source tree. Keep this file in sync
with the copies in sprezzature-colors/scripts/_argparse.py etc. by hand,
and bump ``SKILL_VERSION`` in every copy at release time; this repo has no
automated drift check for it yet.

Author
------
`Warith Harchaoui, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import argparse

SKILL_VERSION = "1.0.0"


def make_parser(
    prog: str,
    description: str,
    epilog: str | None = None,
) -> argparse.ArgumentParser:
    """Build a pre-configured argparse parser.

    Parameters
    ----------
    prog : str
        Program name shown in ``--help`` (e.g. ``"sprezzature-figures-make"``).
    description : str
        One-paragraph description shown above the options table.
    epilog : str or None, optional
        Text shown below the options table — usually usage examples.

    Returns
    -------
    argparse.ArgumentParser
        Parser with ``-V``/``--version`` pre-attached.
    """
    parser = argparse.ArgumentParser(
        prog=prog,
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {SKILL_VERSION}",
    )
    return parser

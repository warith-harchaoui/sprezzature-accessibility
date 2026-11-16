"""
This package may not promise a Python its dependencies cannot deliver.

The manifest said ``>=3.10``, with no upper bound, while its base dependency
``wallet-helper`` has never published a release reaching 3.14 — sixteen
versions on the index, exactly one of them inside ``>=1.3.2,<2``, and that one
declares ``<3.14``. So ``pip install`` on 3.14 failed on a resolution naming a
package the reader never asked for.

Why it survived: ``sprezzature-audio`` and ``sprezzature-publish`` carried a
guard for this shape and the other nine bricks did not, and the single brick
where an inherited ceiling actually bit was one of the nine. A check that
exists in two places out of eleven holds where it happens to be.

The reasoning — and the two cheaper readings that each produced a confident
false accusation — is in :mod:`_pywindow`, which this file shares with every
other brick.

Author
------
Project maintainers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests._pywindow import CANDIDATES, admits, dependency_names, overreach, promise

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "pyproject.toml"

#: Every base dependency, and the Python minors **at least one accepted
#: release** can be installed on.
#:
#: This is the only question that decides, and it took two wrong answers to
#: get to. Reading the *floor's* window says nothing, because a resolver takes
#: the newest release that fits — that reading accused ``sprezzature-figures``
#: of promising two Pythons it could not deliver, and a later ``dowhy`` lifts
#: the bound. Reading the *newest* window is wrong in the mirror: on 3.10 a
#: resolver installs an old ``numpy``, not today's, so "the newest numpy wants
#: 3.12" says nothing about whether 3.10 works. That reading flagged six
#: bricks, all of them healthy.
#:
#: So what is recorded is reachability: for each candidate minor, does *some*
#: release this manifest accepts admit it. Measured against the simple index
#: on 2026-11-02; re-measure when a floor or a dependency moves.
#:
#: ``wallet-helper`` was the one that stopped short until 2026-11-16, when
#: 1.4.1 (inside ``>=1.3.2,<2``) dropped its ``<3.14``; re-measured that day,
#: and this package's own promise lost its ceiling with it.
MEASURED: dict[str, tuple[str, ...]] = {
    "click": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "best-engine-ai-helper": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "wallet-helper": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "fastapi": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "uvicorn": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "langdetect": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "fastapi-mcp": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "mcp": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    # Added 2026-11-04 with the dependency. Every release from 10.0.0 declares
    # a floor only (>=3.8 up to >=3.11 for 13.0.0) and no ceiling.
    "Pillow": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
}


def test_there_are_dependencies_to_check() -> None:
    """Non-vacuity: an empty manifest would make every assertion below hold."""
    assert len(dependency_names(MANIFEST)) >= 5


def test_every_base_dependency_has_a_measured_window() -> None:
    """A new dependency has to be measured, not assumed.

    This is the half that rots: the comparison is only as complete as the
    table, and a dependency added without a reading would be invisible to it —
    which is how the ceiling this file exists for got in.
    """
    names = set(dependency_names(MANIFEST))
    unmeasured = sorted(names - set(MEASURED))
    assert not unmeasured, (
        "these base dependencies have no recorded reachability, so the check "
        f"below silently skips them: {', '.join(unmeasured)}"
    )
    stale = sorted(set(MEASURED) - names)
    assert not stale, f"recorded and no longer required: {', '.join(stale)}"


@pytest.mark.parametrize("version", CANDIDATES)
def test_the_promise_is_not_wider_than_the_graph(version: str) -> None:
    """For every Python this package claims, every dependency must reach it."""
    broken = overreach(MANIFEST, MEASURED, version)
    assert not broken, (
        f"requires-python = {promise(MANIFEST)!r} claims Python {version}, and "
        f"these cannot be installed there: {', '.join(broken)}.\n"
        "  Either narrow the promise, or raise the dependency to one that "
        "reaches further — the promise is what a reader acts on."
    )


def test_the_check_would_notice_an_overreaching_promise() -> None:
    """Sabotage, inline: the assertion above must fail on the state this file
    was written for — ``>=3.10`` over a ``wallet-helper`` that stops at 3.13.

    The state is rebuilt from a copy of the table rather than read from it:
    the first version of this test asserted the world itself (wallet-helper
    never reaches 3.14), so the day the dependency moved it failed for being
    right, and the guard looked broken when it was the world that changed.
    """
    assert admits(">=3.10", "3.14"), "the specifier reader is wrong"
    assert not admits("<3.14,>=3.10", "3.14"), "the specifier reader is wrong"
    stuck = dict(MEASURED, **{"wallet-helper": ("3.10", "3.11", "3.12", "3.13")})
    assert overreach(MANIFEST, stuck, "3.13") == []
    if admits(promise(MANIFEST), "3.14"):
        assert overreach(MANIFEST, stuck, "3.14"), (
            "a wallet-helper stopping at 3.13 under a promise of 3.14 went unnoticed"
        )

"""
This package may not promise a Python its dependencies cannot deliver.

``requires-python`` is a promise to anyone running ``pip install``. A
dependency's ``requires-python`` is the same promise, one level down, and it
binds this package just as hard: if ``wallet-helper`` cannot be installed on
3.14, nothing that requires ``wallet-helper`` can be either — whatever this
manifest says.

The manifest said ``>=3.10``, with no upper bound, while its base dependency
``wallet-helper`` declared ``<3.14,>=3.10`` at every version the floor
permits. So the promise was wider than the graph, and an installer on 3.14
would have failed with a resolution error naming a package the reader never
asked for.

Why it survived
---------------
``sprezzature-audio`` and ``sprezzature-publish`` carry a guard for this exact
shape; the other nine bricks do not. Measured on 2026-11-02 across all eleven:
the single brick where an inherited ceiling actually bit was one of the nine
without a guard. A check that exists in two places out of eleven is a check
that holds wherever it happens to be.

Offline on purpose
------------------
The windows below are **recorded**, not fetched, and they record which Pythons
a dependency can actually be installed on — see :data:`MEASURED`, where two
cheaper readings each produced a confident and false accusation. A test that queries PyPI is a
test that fails on a runner with no network and passes for the wrong reason
behind a proxy. Re-measure by hand when a floor moves — the command is in
:data:`MEASURED`'s own comment — which is the same discipline
``test_a_capped_extra_says_so.py`` uses next door.

Author
------
Project maintainers.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

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
#: ``wallet-helper`` is the one that stops short, and it is why this package's
#: own promise now ends at 3.14: every published release declares ``<3.14``,
#: and ``>=1.3.2,<2`` admits exactly one of them.
MEASURED: dict[str, tuple[str, ...]] = {
    "click": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "best-engine-ai-helper": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "wallet-helper": ("3.10", "3.11", "3.12", "3.13"),
    "fastapi": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "uvicorn": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "langdetect": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "fastapi-mcp": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
    "mcp": ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15"),
}

#: The minor versions to check the promise against. 3.14 is the one that
#: exists and is excluded by the ceiling above; 3.15 is here so a ceiling
#: moving to ``<3.15`` is noticed before the interpreter ships.
CANDIDATES: tuple[str, ...] = ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15")


#: Deliberately regex, not ``tomllib``.
#:
#: ``tomllib`` landed in 3.11 and this package's floor is **3.10**, so an
#: import of it fails at *collection* on the oldest interpreter in the matrix
#: — which is what happened: green on this machine's 3.13, red on the
#: runner's 3.10, with a ``ModuleNotFoundError`` that names no test. The two
#: shapes read here are a quoted scalar and a flat array of strings, neither
#: of which needs a parser.
_REQUIRES_PYTHON = re.compile(r'^requires-python\s*=\s*"([^"]+)"', re.M)
_DEPENDENCIES = re.compile(r"^dependencies\s*=\s*\[(.*?)^\]", re.S | re.M)


def _promise() -> str:
    found = _REQUIRES_PYTHON.search(MANIFEST.read_text(encoding="utf-8"))
    assert found, "pyproject.toml declares no requires-python"
    return found.group(1)


def _names() -> list[str]:
    block = _DEPENDENCIES.search(MANIFEST.read_text(encoding="utf-8"))
    assert block, "pyproject.toml has no [project] dependencies array"
    # Comments inside the array quote specifiers too, so they go first.
    body = re.sub(r"#[^\n]*", "", block.group(1))
    return [
        re.split(r"[<>=~\[; !]", m.group(1))[0].strip()
        for m in re.finditer(r'"([^"]+)"', body)
    ]


def _admits(specifier: str, version: str) -> bool:
    """Whether a ``requires-python`` string admits this minor version."""
    from packaging.specifiers import SpecifierSet

    if not specifier:
        return True
    return SpecifierSet(specifier).contains(f"{version}.0")


def test_there_are_dependencies_to_check() -> None:
    """Non-vacuity: an empty manifest would make every assertion below hold."""
    assert len(_names()) >= 5, f"only {len(_names())} base dependencies found"


def test_every_base_dependency_has_a_measured_window() -> None:
    """A new dependency has to be measured, not assumed.

    This is the half that rots: the comparison below is only as complete as
    the table, and a dependency added without a reading would be invisible to
    it — which is precisely how the ceiling this file exists for got in.
    """
    unmeasured = sorted(set(_names()) - set(MEASURED))
    assert not unmeasured, (
        "these base dependencies have no recorded requires-python, so the "
        f"check below silently skips them: {', '.join(unmeasured)}"
    )
    stale = sorted(set(MEASURED) - set(_names()))
    assert not stale, f"these are recorded and no longer required: {', '.join(stale)}"


@pytest.mark.parametrize("version", CANDIDATES)
def test_the_promise_is_not_wider_than_the_graph(version: str) -> None:
    """For every Python this package claims, every dependency must allow it."""
    promise = _promise()
    if not _admits(promise, version):
        return                      # not claimed, so nothing to keep
    broken = sorted(
        f"{name} (reaches {', '.join(reach) or 'nothing'})"
        for name, reach in MEASURED.items()
        if name in _names() and version not in reach
    )
    assert not broken, (
        f"requires-python = {promise!r} claims Python {version}, and these "
        f"dependencies cannot be installed there: {', '.join(broken)}.\n"
        "  Either lower the promise to match, or raise the dependency to a "
        "version that reaches further — the promise is the one a reader acts on."
    )


def test_the_check_would_notice_an_overreaching_promise() -> None:
    """Sabotage, inline: the assertion above must fail on the state this file
    was written for — ``>=3.10`` with `wallet-helper` capped at ``<3.14``."""
    assert _admits(">=3.10", "3.14"), "the specifier reader is wrong"
    assert not _admits("<3.14,>=3.10", "3.14"), "the specifier reader is wrong"
    assert "3.14" not in MEASURED["wallet-helper"], (
        "wallet-helper is recorded as reaching 3.14; re-measure before trusting this"
    )
    assert _admits(_promise(), "3.13")
    assert not _admits(_promise(), "3.14"), (
        "this manifest still claims 3.14 while wallet-helper excludes it"
    )

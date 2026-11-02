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
The windows below are **recorded**, not fetched, and they record the newest
release this manifest accepts rather than its floor — see :data:`MEASURED`,
where reading floors instead produced a confident and false accusation
against a sibling. A test that queries PyPI is a
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
import tomllib

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "pyproject.toml"

#: Every base dependency, and the ``requires-python`` of the **newest release
#: this manifest's specifier admits** — not the floor's.
#:
#: The distinction is the whole correctness of this file, and the first
#: version got it wrong. A floor is not a pin: ``>=3.8,<3.12`` on a floor
#: release says nothing about whether the package can be installed on 3.12,
#: because a resolver takes the newest release that fits, not the oldest.
#: Reading floors flagged ``sprezzature-figures`` as promising two Pythons it
#: could not deliver, and the claim was false — a later ``dowhy`` lifts the
#: bound. Measuring the wrong thing produces a confident accusation, which is
#: worse than measuring nothing.
#:
#: So the question recorded here is the one that decides: *is there any
#: version this manifest accepts that installs on Python X?* Measured on
#: 2026-11-02 against the simple index::
#:
#:     for each dep: releases matching the specifier, newest first,
#:     keep the first whose requires-python admits X
#:
#: ``""`` means the release declares no bound, which admits everything.
MEASURED: dict[str, str] = {
    "click": "",
    "best-engine-ai-helper": ">=3.10",
    # Every published wallet-helper declares `<3.14`, and the only release
    # this manifest's `>=1.3.2,<2` accepts is 1.3.2 itself. So there is no
    # version of it that installs on 3.14 — which is why the ceiling below is
    # inherited rather than chosen, and why the promise had to narrow.
    "wallet-helper": "<3.14,>=3.10",
    "fastapi": "",
    "uvicorn": "",
    "langdetect": "",
    "fastapi-mcp": "",
    "mcp": "",
}

#: The minor versions to check the promise against. 3.14 is the one that
#: exists and is excluded by the ceiling above; 3.15 is here so a ceiling
#: moving to ``<3.15`` is noticed before the interpreter ships.
CANDIDATES: tuple[str, ...] = ("3.10", "3.11", "3.12", "3.13", "3.14", "3.15")


def _project() -> dict:
    return tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["project"]


def _names() -> list[str]:
    return [re.split(r"[<>=~\[; !]", d)[0].strip() for d in _project()["dependencies"]]


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
    promise = _project()["requires-python"]
    if not _admits(promise, version):
        return                      # not claimed, so nothing to keep
    broken = sorted(
        f"{name} ({window})"
        for name, window in MEASURED.items()
        if name in _names() and not _admits(window, version)
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
    assert _admits(_project()["requires-python"], "3.13")
    assert not _admits(_project()["requires-python"], "3.14"), (
        "this manifest still claims 3.14 while wallet-helper excludes it"
    )

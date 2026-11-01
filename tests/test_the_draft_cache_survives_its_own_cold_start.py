"""
The caller retries its own cache's constructor, and here is the version of
``wallet-helper`` that makes it necessary.

The defect, which is upstream
-----------------------------
``wallet-helper`` up to and including **1.3.1** — the newest release on PyPI as
this is written — runs ``PRAGMA journal_mode=WAL`` inside
``SqliteLedger.__init__``. Going into WAL needs exclusive access to the database
file, and SQLite answers a journal-mode change with ``SQLITE_BUSY`` *without
consulting the busy handler*, so the thirty-second timeout that connection sets
does not cover that one statement.

Three processes opening a cold ledger in the same instant therefore leave one
dead on ``database is locked`` — and three processes drafting the same image is
precisely the case the ledger exists for.
``test_two_drafts_of_one_image_cost_one_call.py`` spawns exactly that, and
measured it at **3 failures in 15 runs**.

Fixed upstream in 1.3.2 by reading the mode before writing it. But a fix nobody
can install is not a fix: this package's CI resolves ``wallet-helper>=1.3,<2``
from the index, and the index serves 1.3.1. So ``_open_ledger`` defends the
caller against the version it actually gets — measured with the 1.3.1 code
path in place: **0 failures in 15 runs**.

The pattern is the siblings', not a new one
-------------------------------------------
``sprezzature-audio`` and ``sprezzature-publish`` already carry this retry in
their ``scripts/_wallet.py``, with these constant names and these numbers, and
their own test for it says "the creation race, which cost a sibling repository
a red run" — the sibling it cost was this one. The first version of this file
reinvented it, divergently and worse: a fixed backoff where theirs is jittered
(three processes retrying in lockstep collide again on the next rung), and a
``RuntimeError`` where theirs **degrades** to the JSON ledger. Raising trades a
cache for a crash, and the crash was the defect.

So this tests the siblings' behaviour, and ``_open_ledger`` is their code.

Why these assertions and not a race
-----------------------------------
The window is narrower than a test can aim at — three shapes of deliberate
contention were tried upstream and none reproduced it, because the busy handler
*does* apply to ordinary lock waits. So the error is injected, which also makes
these deterministic. The real concurrency is still covered next door; this file
covers the retry.

They fail for different reasons, which is the point of having several: a retry
that gives up on the first refusal would not survive the race it is written
for; one that never stops would hang a command line; a run that *raises* on
exhaustion loses the draft entirely where it could have lost only the
cross-process single-flight; and a warning that does not say what happened
leaves the reader with ``database is locked`` and no handle.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# ``scripts/`` is already on sys.path: tests/conftest.py puts it there so the
# test modules import these scripts the way the scripts import each other.
# Hence the `noqa`: the import is deliberately below that arrangement.
import alt_from_ollama as alt  # noqa: E402
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


class _LockedUntil:
    """A ledger class that refuses to be constructed a given number of times."""

    def __init__(self, refusals: int) -> None:
        self.left = refusals
        self.attempts = 0
        self.opened_with: dict | None = None

    def __call__(self, db, **kwargs):
        self.attempts += 1
        if self.left > 0:
            self.left -= 1
            raise sqlite3.OperationalError("database is locked")
        self.opened_with = {"db": db, **kwargs}
        return self


def test_a_transient_lock_is_waited_out(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two refusals then a success, and the ledger comes back.

    Before ``_open_ledger`` this was a dead subprocess: the constructor's
    ``OperationalError`` travelled all the way out of ``describe``, so a run
    that lost the race produced no draft at all rather than a slower one.
    """
    monkeypatch.setattr(alt, "OPEN_BACKOFF", 0.0)
    fake = _LockedUntil(refusals=2)

    opened = alt._open_ledger(fake, tmp_path / "ledger.db")

    assert opened is fake, "the ledger that was finally opened is not the one returned"
    assert fake.attempts == 3, f"expected two refusals then a success, got {fake.attempts}"
    assert fake.opened_with == {
        "db": tmp_path / "ledger.db",
        "max_entries": alt.CACHE_MAX_ENTRIES,
    }, (
        f"the retry changed the arguments: {fake.opened_with}. A retry that opens a "
        f"different ledger than the first attempt would silently drop the size cap."
    )


def test_it_degrades_to_the_json_ledger_instead_of_raising(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A permanent refusal costs the single-flight, not the draft.

    This is the assertion that separates the siblings' pattern from the one
    this file first had. Raising on exhaustion would turn a cache that could
    not be opened into a run that produced nothing — which is exactly the
    failure being fixed, re-entered through the fix. What is lost instead is
    only cross-process single-flight; the memoization and the result survive,
    and the tool answers.

    Also checks the ladder is walked to its end: stopping early loses the race
    the retry exists to win, and never stopping hangs a command line on a lock
    that is not going to clear.
    """
    monkeypatch.setattr(alt, "OPEN_ATTEMPTS", 3)
    monkeypatch.setattr(alt, "OPEN_BACKOFF", 0.0)
    fake = _LockedUntil(refusals=10_000)

    opened = alt._open_ledger(fake, tmp_path / "ledger.db")

    from wallet_helper.ledger import Ledger

    assert isinstance(opened, Ledger), (
        f"a ledger that cannot be opened returned {type(opened).__name__} rather "
        f"than degrading to the JSON ledger. Raising here trades a cache for a "
        f"crash, and the crash is the defect this exists for."
    )
    assert fake.attempts == 3, (
        f"tried {fake.attempts} times for a three-attempt budget — early is a "
        f"lost race, never is a hung command"
    )


def test_a_corrupt_file_is_not_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file that is not a database degrades at once, with its own reason.

    No number of retries repairs a bad file, so retrying one is pure latency on
    a path that is already failing. The two cases have to be told apart in the
    right order, because ``OperationalError`` is a subclass of
    ``DatabaseError`` — swap the ``except`` clauses and a lock stops being
    retried at all, which is the whole feature, silently.
    """
    monkeypatch.setattr(alt, "OPEN_ATTEMPTS", 6)
    monkeypatch.setattr(alt, "OPEN_BACKOFF", 0.0)

    attempts = {"n": 0}

    def corrupt(_db, **_kwargs):
        attempts["n"] += 1
        raise sqlite3.DatabaseError("file is not a database")

    alt._open_ledger(corrupt, tmp_path / "ledger.db")
    assert attempts["n"] == 1, (
        f"a corrupt file was tried {attempts['n']} times. Only a lock is worth "
        f"waiting on; retrying corruption is latency on a path already lost."
    )


def test_the_warning_names_the_version_and_what_was_lost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``database is locked`` is not actionable. This warning is.

    Three things a reader needs and would otherwise have to find out: what was
    lost (the cross-process single-flight, and only that), that the cause is a
    known upstream defect, and which release fixes it. On stderr rather than
    raised, because the run continues — a silent degradation would be worse
    than the crash it replaces.
    """
    monkeypatch.setattr(alt, "OPEN_ATTEMPTS", 1)
    monkeypatch.setattr(alt, "OPEN_BACKOFF", 0.0)

    alt._open_ledger(_LockedUntil(refusals=10_000), tmp_path / "ledger.db")

    said = capsys.readouterr().err
    for needed in ("1.3.2", "single-flight", "JSON ledger"):
        assert needed in said, (
            f"the warning does not mention {needed!r}, so a reader hitting it has "
            f"to go and find out. Full text: {said!r}"
        )


def test_the_floor_still_allows_the_version_that_needs_this() -> None:
    """When the floor moves past 1.3.1, this whole file should go.

    A compatibility shim with no removal condition becomes permanent by
    default. This is that condition, as an assertion: the day the manifest
    names ``wallet-helper>=1.3.2`` or later, the defect is unreachable and
    ``_open_ledger`` can collapse back to a plain constructor call.
    """
    import re

    manifest = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    found = re.search(r'"wallet-helper>=([0-9][0-9.]*)', manifest)
    assert found, "pyproject.toml names no wallet-helper floor"
    floor = tuple(int(part) for part in found.group(1).split("."))
    assert floor < (1, 3, 2), (
        f"the floor is now wallet-helper>={found.group(1)}, which carries the "
        f"journal-mode fix. `_open_ledger` in scripts/alt_from_ollama.py and "
        f"this whole file exist only to survive 1.3.1 — delete both."
    )

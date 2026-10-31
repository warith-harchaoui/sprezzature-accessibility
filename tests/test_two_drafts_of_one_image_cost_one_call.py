"""
Two drafting runs on one cold image call the model once, not twice.

The cache this replaced was content-addressed and survived restarts, and both
of those were right. What it had no way of doing was single-flight. Its read
was ``path.is_file()`` and its write came after the model answered, so two
runs that started together both found nothing, both called the model, and the
second one's answer overwrote the first's. Measured on this machine with
three runs on one image: three calls, 7 ms apart. Nothing was wrong with the
output — it just cost three times what it had to, and the window is as wide
as a model call is long, which for a vision model is seconds.

Three sessions working side by side is a normal afternoon here, so this is
not a thought experiment; it is the bill.

Why a subprocess and not two threads: an in-process lock would pass a
threaded version of this test and change nothing about the defect. The claim
is about separate interpreters sharing one ledger file, so the guard has to
take the shape of the defect and spawn them.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "images"

#: How long the stand-in model call takes. The real one is seconds; this has
#: only to be long enough that three interpreters are inside it at once, and
#: the measured gap between their arrivals was 7 ms.
_MODEL_SECONDS = 1.0

#: One drafting run: point the module's cache at the shared directory, stub
#: the model with something that records the fact it was called, and draft.
_RUN = r"""
import os, sys, time
sys.path.insert(0, sys.argv[1])
import alt_from_ollama as alt

alt.CACHE_DIR = __import__("pathlib").Path(sys.argv[2])
alt.NO_CACHE = False
seconds = float(sys.argv[4])
log = sys.argv[5]


def stub(*a, **k):
    with open(log, "a") as fh:
        fh.write(f"{os.getpid()}\n")
    time.sleep(seconds)
    return "A bar chart of quarterly revenue"


alt._llm_chat = stub
print(alt.describe(sys.argv[3], kind="informative", lang="en", model="m:tag"))
"""


@pytest.fixture
def shared(tmp_path):
    """A cache directory and a call log the parallel runs both reach."""
    image = tmp_path / "subject.png"
    image.write_bytes((FIXTURES / "chart-bar.png").read_bytes())
    return tmp_path / "ledger-dir", image, tmp_path / "calls.log"


def _launch(cache_dir: Path, image: Path, log: Path, seconds: float) -> subprocess.Popen:
    return subprocess.Popen(
        [
            sys.executable,
            "-c",
            _RUN,
            str(REPO_ROOT / "scripts"),
            str(cache_dir),
            str(image),
            str(seconds),
            str(log),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_three_runs_started_together_share_one_model_call(shared) -> None:
    """The exact experiment the hand-rolled cache failed, run on the new one."""
    cache_dir, image, log = shared
    procs = [_launch(cache_dir, image, log, _MODEL_SECONDS) for _ in range(3)]
    outs = []
    for p in procs:
        out, err = p.communicate(timeout=180)
        assert p.returncode == 0, err[-800:]
        outs.append(out.strip())

    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    assert len(calls) == 1, (
        f"three parallel runs on one cold image made {len(calls)} model calls; "
        "the point of the ledger is that the two that arrive second wait for "
        "the first one's answer instead of buying their own"
    )
    # And they all got the answer — waiting is not the same as failing.
    assert outs == ["A bar chart of quarterly revenue"] * 3


def test_a_later_run_pays_nothing(shared) -> None:
    """The warm case, from a separate interpreter: the ledger outlives both."""
    cache_dir, image, log = shared
    first = _launch(cache_dir, image, log, 0.0)
    out, err = first.communicate(timeout=180)
    assert first.returncode == 0, err[-800:]
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1

    second = _launch(cache_dir, image, log, 0.0)
    out2, err2 = second.communicate(timeout=180)
    assert second.returncode == 0, err2[-800:]
    assert out2.strip() == out.strip()
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1, (
        "a fresh interpreter recomputed a draft the ledger already held"
    )

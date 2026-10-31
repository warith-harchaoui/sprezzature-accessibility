"""
The fixtures README has to describe guards that exist.

Two of its claims were false for months, and both were the same shape as
this repository's dominant defect: a mechanism is described in prose, and
nothing implements it.

1. *"Image bytes | `wiki/*.jpg`, `wiki/*.png` | no — gitignored"*. There
   was no such rule in ``.gitignore``. The bytes were merely untracked,
   which looks identical in a clean tree and nothing like it once a
   fetch has run: two of them sat in ``git status`` for days, and the
   catalogue's ``functional`` entry is the Wikipedia globe, a Wikimedia
   trademark kept under fair use for test fixtures only. "Nobody has
   typed ``git add`` on it yet" is not a guard.

2. *"CI performs it as part of the eval-suite job"*. There is no
   eval-suite job. The workflow defines one ``test`` job ending in
   ``pytest -q``, and ``addopts`` carries ``-m "not eval"``, so
   ``tests/eval/`` is deselected there and the fetcher is never called.
   The suite is a local opt-in, which is the right design — it needs
   Ollama, weights and ``deepeval`` — but the README promised a gate
   that nothing ran.

So these assertions are about agreement between the prose and the files
it describes, in both directions: wiring a real eval job later should
make the README wrong here, not quietly leave it stale.

The third assertion is the one that keeps the fix honest. The ignore
rule must cover the regenerable bytes and must *not* swallow
``wiki/truth.json``: the manifest is the source of truth, it is what the
eval module reads to decide what gets evaluated, and an over-broad
``wiki/*`` would make a partial manifest invisible instead of merely
quiet.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import re
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

GITIGNORE = ROOT / ".gitignore"
FIXTURES_README = ROOT / "tests" / "fixtures" / "images" / "README.md"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"

#: The regenerable Wikimedia bytes, as repository-relative paths. Both
#: extensions are present in the catalogue: two JPEG thumbnails and two
#: PNG renditions of SVG sources.
REGENERABLE = (
    "tests/fixtures/images/wiki/marie-curie-portrait.jpg",
    "tests/fixtures/images/wiki/tour-eiffel.jpg",
    "tests/fixtures/images/wiki/climate-temperature-chart.png",
    "tests/fixtures/images/wiki/wikipedia-logo.png",
)

#: The manifest, which must stay committable.
MANIFEST = "tests/fixtures/images/wiki/truth.json"


def _ignore_patterns() -> list[str]:
    """Return the non-comment, non-blank patterns declared in .gitignore."""
    lines = GITIGNORE.read_text(encoding="utf-8").splitlines()
    return [
        stripped for line in lines if (stripped := line.strip()) and not stripped.startswith("#")
    ]


def _is_ignored(path: str) -> bool:
    """
    Whether ``path`` matches any .gitignore pattern.

    A deliberately small subset of gitignore semantics — enough for the
    anchored, explicit patterns this repository uses, and hermetic (no
    ``git`` subprocess, so the check cannot degrade into a skip on a
    machine or image without git).
    """
    for pattern in _ignore_patterns():
        if pattern.startswith("!"):  # negation: out of scope here
            continue
        candidate = pattern.rstrip("/")
        if fnmatch(path, candidate):
            return True
        # A bare directory or name pattern matches at any depth.
        if "/" not in candidate and any(fnmatch(segment, candidate) for segment in path.split("/")):
            return True
    return False


def test_the_fetched_image_bytes_are_really_ignored() -> None:
    """
    The README's "gitignored" column must correspond to a real rule.

    Checked per file rather than per pattern: what matters is that these
    bytes cannot be committed by accident, not which glob achieves it.
    """
    missing = [path for path in REGENERABLE if not _is_ignored(path)]
    assert not missing, (
        "The fixtures README lists these as gitignored, but no .gitignore "
        f"rule matches them: {missing}. Untracked is not ignored — one of "
        "the catalogue entries is a Wikimedia trademark held under fair use "
        "for test fixtures only."
    )


def test_the_truth_manifest_is_not_swallowed_by_the_ignore_rule() -> None:
    """
    ``wiki/truth.json`` stays tracked: it is the ground truth itself.

    An over-broad rule (``tests/fixtures/images/wiki/`` or ``wiki/*``)
    would ignore the manifest too, and the eval module reads the manifest
    to decide what it evaluates — losing it from the index would make the
    catalogue a property of whoever last ran the fetcher.
    """
    assert not _is_ignored(MANIFEST), (
        f"{MANIFEST} is matched by a .gitignore rule. The manifest is the "
        "source of truth for the eval catalogue and must stay committed; "
        "narrow the rule to the image extensions."
    )


def test_the_readme_and_the_workflow_agree_about_the_eval_job() -> None:
    """
    The README may claim a CI eval job only if the workflow defines one.

    Asserted as a biconditional so it stays useful in both directions: if
    an eval job is ever wired up, this fails and sends the author back to
    the paragraph that currently says there is none.
    """
    workflow = WORKFLOW.read_text(encoding="utf-8")
    readme = FIXTURES_README.read_text(encoding="utf-8")

    # A job that genuinely exercises the eval suite either opts into the
    # marker or populates the fixtures first. Neither appears today.
    workflow_runs_eval = bool(
        re.search(r"-m\s+[\"']?eval", workflow) or "fetch_wikipedia" in workflow
    )
    readme_disclaims_ci = "CI does not run this suite" in readme

    assert workflow_runs_eval is not readme_disclaims_ci, (
        "The fixtures README and .github/workflows/ci.yml disagree about "
        f"the eval suite. workflow_runs_eval={workflow_runs_eval}, "
        f"readme_disclaims_ci={readme_disclaims_ci}. Either the workflow "
        "gained an eval job and the README's disclaimer is now stale, or "
        "the disclaimer was removed while CI still never runs the suite."
    )

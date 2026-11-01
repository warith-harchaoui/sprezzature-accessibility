"""
The pre-commit install, measured instead of promised.

Why this exists
---------------
This package's argument for itself is that the lint "is stdlib-only on purpose:
it runs in milliseconds in a minimal CI container and in a pre-commit hook,
which is the reason anyone reaches for it over axe-core". On 2026-11-01 every
extra in the suite was folded into the base install, so
``pip install sprezzature-accessibility`` went from **1 package to 57** --
measured -- and most of those 57 are the HTTP and MCP surfaces, which a hook
has no use for.

The install half of the argument was spent. ``test_the_lint_stays_out_of_the_extra``
keeps the import half: the lint still loads nothing but click. This file keeps
the install half, and it does it without reintroducing an extra, because the
owner's decision is one ``pip install`` for the product and it is the right
one -- a reader should not have to know a magic word before the package works.

What a hook does instead
------------------------
``pip install --no-deps`` plus click. Three packages, measured here rather than
asserted: pip, click, and this one. The lint path imports nothing else, so
there is nothing to miss -- and that is exactly the claim this test turns from
prose into a fact, by running the shipped console script against a page with a
known defect and checking it is found.

This is also why the two halves have to be separate tests. The import guard
would still pass on a 57-package install that the hook never wanted; this one
would still pass if the lint quietly grew a module-level import of something
pip happens to have installed anyway. Each catches what the other cannot.

Cost
----
Builds and installs the package in a throwaway venv, so a few tens of seconds.
It carries no marker and so runs in CI on every push, deliberately: the
guard exists because the promise is easy to break by accident, and a guard
behind a marker nobody selects is a promise with no guard at all.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import subprocess
import sys
import venv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: pip, click, and this package. Anything else and the hook is paying for
#: something it does not run.
EXPECTED_PACKAGES = 3

PAGE = """<!doctype html>
<html lang="en"><head><title>t</title></head>
<body><img src="a.png"></body></html>
"""


@pytest.fixture(scope="module")
def hook_venv(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A venv holding the package with no dependencies, plus click."""
    root = tmp_path_factory.mktemp("hook")
    env = root / "venv"
    venv.create(env, with_pip=True)
    python = env / ("Scripts" if sys.platform == "win32" else "bin") / "python"
    for args in (["--no-deps", str(REPO_ROOT)], ["click>=8.1"]):
        done = subprocess.run(
            [str(python), "-m", "pip", "install", "-q", *args],
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert done.returncode == 0, f"pip install {args} failed:\n{done.stderr[-800:]}"
    return env


def _bin(env: Path, name: str) -> Path:
    return env / ("Scripts" if sys.platform == "win32" else "bin") / name


def test_the_hook_install_is_three_packages(hook_venv: Path) -> None:
    """Three, named. A count alone would not say *which* three.

    The names matter more than the number: a run that happened to install
    `requests` and drop `click` would also count three.
    """
    done = subprocess.run(
        [str(_bin(hook_venv, "python")), "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert done.returncode == 0, done.stderr[-400:]
    installed = {
        line.split("==")[0].lower().replace("_", "-")
        for line in done.stdout.splitlines()
        if line.strip()
    }
    assert installed == {"pip", "click", "sprezzature-accessibility"}, (
        f"the hook install is {sorted(installed)}. It has to be pip, click and "
        f"this package: anything else is weight a pre-commit hook pays for and "
        f"never runs. If the lint genuinely needs a new dependency, say so here "
        f"and in the README -- the number in both is the promise."
    )
    assert len(installed) == EXPECTED_PACKAGES


def test_the_lint_runs_and_finds_a_real_defect(hook_venv: Path, tmp_path: Path) -> None:
    """Installed that way, the console script works on a real page.

    A page with exactly one defect, so the finding is unambiguous. Before this,
    nothing proved the minimal install was *usable* -- only that the import
    graph was clean, which is a different claim and would hold on a package
    that could not run at all.
    """
    page = tmp_path / "page.html"
    page.write_text(PAGE, encoding="utf-8")

    done = subprocess.run(
        [str(_bin(hook_venv, "sprezzature-accessibility-lint")), str(page)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert "img-missing-alt" in done.stdout, (
        f"the lint did not report the missing alt on a minimal install.\n"
        f"stdout: {done.stdout[-600:]}\nstderr: {done.stderr[-600:]}"
    )


def test_the_readme_documents_the_hook_install(hook_venv: Path) -> None:
    """The install line has to be written down where a reader looks for it.

    Not decoration: the hook install is only discoverable if it is documented,
    and a documented command that drifts from the tested one is worse than an
    undocumented one. Both READMEs are checked, because this package ships in
    two languages and a promise kept in one of them is kept by half.
    """
    missing = [
        name
        for name in ("README.md", "LISEZMOI.md")
        if "--no-deps" not in (REPO_ROOT / name).read_text(encoding="utf-8")
    ]
    assert not missing, (
        f"{missing} do not document the `--no-deps` install that this file "
        f"tests. A reader reaching for the lint from a pre-commit hook has no "
        f"way to discover it, and will install 57 packages to run one."
    )

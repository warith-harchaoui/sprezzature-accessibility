"""
Nothing on the lint path may load a drafting dependency.

The argument this package is chosen on is written in its own manifest: the
lint "is stdlib-only on purpose: it runs in milliseconds in a minimal CI
container and in a pre-commit hook, which is the reason anyone reaches for it
over axe-core". The drafting half is behind an extra precisely so a
pre-commit install does not pull a model client to run a check that never
calls one.

That is an argument about an import graph, and until now nothing measured it.
It became worth measuring the day the extra grew: the drafts are memoized
through ``wallet-helper`` now, so ``[alt]`` holds two third-party packages
where it held one, and the way that argument dies is not a decision anybody
takes — it is one module-level ``import`` in a file the lint happens to
touch. The cost would be invisible here and visible to everybody else: a hook
that took milliseconds starts resolving 62 MB of wheels.

Three subjects, because they fail apart:

``lint_a11y``
    The module behind ``sprezzature-accessibility-lint``, the per-tool
    console script, the one a hook names.
``sprezzature_accessibility.cli``
    The group. It carries the drafting sub-commands in its table, so it is
    the natural place for someone to import the drafter at module level in
    order to describe it.
``alt_from_ollama``
    The drafter itself, which must *also* import clean — not because the lint
    needs it to, but because ``make-alt --help`` has to answer on a bare
    install. Both heavy imports in it are deferred to first use for that
    reason (``_llm_chat``, ``_wallet``); this is what says so.

What changed on 2026-11-01, and why this file matters more now
--------------------------------------------------------------
``[alt]`` is gone. Every extra in the suite was folded into its package's
base install, so ``best-engine-ai-helper`` and ``wallet-helper`` arrive with
``pip install sprezzature-accessibility`` whether a reader wants the drafter
or not.

**That costs the install half of the argument above, and it is worth saying
plainly rather than quietly.** A pre-commit install is no longer a minimal
one. What survives is the half this file measures: the *import graph*. The
lint still loads nothing but click, so the hook still runs in milliseconds —
and this file is now the only thing standing between that and one
module-level ``import`` in a file the lint happens to touch. Before, a
careless import cost a reader who had opted in to the drafter. Now it costs
everybody, on every run of the hook.

The forbidden list was read out of the extra; it is named here instead,
because there is no extra to read. :func:`test_every_drafting_distribution_is_declared`
keeps the names honest against the manifest, so a rename or a removal fails
here rather than silently emptying the set — a guard whose subject resolves
to nothing passes forever. Read with a regex, not ``tomllib``, which is
stdlib only from 3.11 while this package supports 3.10.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Prints every top-level module name loaded after importing ``argv[1]``.
#: Run as a subprocess because the question is about a *fresh* interpreter:
#: inside pytest half the suite has already imported the drafter.
_PROBE = r"""
import json, sys
name = sys.argv[1]
if name:
    __import__(name)
print(json.dumps(sorted(n for n in sys.modules if "." not in n)))
"""


#: The distributions only the drafting half needs. ``click`` is deliberately
#: not here: the lint's own command line is click, so loading it proves
#: nothing and would fail this on a correct install.
DRAFTING_DISTRIBUTIONS = ("best-engine-ai-helper", "wallet-helper")


def _declared_in_base() -> set[str]:
    """Distribution names in ``dependencies = [...]``, read with a regex."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    base = re.search(r"^dependencies = \[(.*?)^\]", text, re.MULTILINE | re.DOTALL)
    assert base, "no `dependencies = [...]` in pyproject.toml"
    return {
        n.lower() for n in re.findall(r'^\s*"([A-Za-z0-9._-]+)', base.group(1), re.MULTILINE)
    }


def _drafting_imports() -> set[str]:
    """The forbidden import names.

    PyPI spells distributions with hyphens and Python imports them with
    underscores; both of these follow that rule.
    """
    return {n.replace("-", "_").lower() for n in DRAFTING_DISTRIBUTIONS}


def _modules_loaded_by(name: str) -> set[str]:
    """Top-level modules a fresh interpreter holds after importing *name*."""
    done = subprocess.run(
        [sys.executable, "-c", _PROBE, name],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env={"PYTHONPATH": f"{REPO_ROOT / 'scripts'}:{REPO_ROOT}", "PATH": "/usr/bin:/bin"},
        timeout=120,
    )
    assert done.returncode == 0, f"importing {name!r} failed:\n{done.stderr[-800:]}"
    return set(json.loads(done.stdout))


def test_every_drafting_distribution_is_declared() -> None:
    """The forbidden list is written here, so check it against the manifest.

    A guard whose subject resolves to nothing passes forever. The list used to
    be *derived* from the ``[alt]`` extra, which answered this for free; with
    the extra folded into the base there is nothing to derive it from, so the
    names are checked instead. A rename or a removal fails here rather than
    leaving three green tests about an empty set.
    """
    base = _declared_in_base()
    missing = [name for name in DRAFTING_DISTRIBUTIONS if name.lower() not in base]
    assert not missing, (
        f"{missing} are named as drafting dependencies and the base install "
        f"does not declare them. Either they were renamed -- update "
        f"DRAFTING_DISTRIBUTIONS -- or the drafter lost a dependency and the "
        f"three tests below are now checking an emptier set than they look."
    )


@pytest.mark.parametrize(
    "module",
    ["lint_a11y", "sprezzature_accessibility.cli", "alt_from_ollama"],
)
def test_importing_it_loads_no_drafting_dependency(module: str) -> None:
    """Importing *module* must not drag the drafting half's dependencies in."""
    forbidden = _drafting_imports() & _modules_loaded_by(module)
    assert not forbidden, (
        f"importing {module!r} loaded {sorted(forbidden)}, which only the "
        "drafting half needs. Defer the import to first use, the way "
        "`_llm_chat` and `_wallet` do: the lint is chosen for running in "
        "milliseconds in a pre-commit hook, and a module-level import here "
        "ends that quietly -- for everybody, since 2026-11-01, because these "
        "packages are in the base install now and no longer opted into."
    )

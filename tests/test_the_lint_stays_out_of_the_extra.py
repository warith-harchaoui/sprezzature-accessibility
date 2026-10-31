"""
Nothing on the lint path may load a package from the ``[alt]`` extra.

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

The forbidden list is read out of ``[project.optional-dependencies] alt`` in
pyproject.toml rather than written here, so a package added to that extra
tomorrow is covered tonight without anybody remembering this file. Read with
a regex, not ``tomllib``, which is stdlib only from 3.11 while this package
supports 3.10.

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


def _alt_extra_imports() -> set[str]:
    """Import names of the ``[alt]`` extra, minus what the base install has.

    ``click`` is in both: the extra repeats it and ``dependencies`` requires
    it, so it is not evidence of anything and would make this test fail on a
    bare install.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^alt = \[(.*?)^\]", text, re.MULTILINE | re.DOTALL)
    assert block, "no `alt = [...]` extra in pyproject.toml"
    names = set(re.findall(r'^\s*"([A-Za-z0-9._-]+)', block.group(1), re.MULTILINE))
    base = re.search(r"^dependencies = \[(.*?)^\]", text, re.MULTILINE | re.DOTALL)
    assert base, "no `dependencies = [...]` in pyproject.toml"
    names -= set(re.findall(r'^\s*"([A-Za-z0-9._-]+)', base.group(1), re.MULTILINE))
    # PyPI spells distributions with hyphens and Python imports them with
    # underscores; every member of this extra follows that rule.
    return {n.replace("-", "_").lower() for n in names}


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


def test_the_extra_names_something_the_base_install_does_not() -> None:
    """The forbidden list is derived, so first check it is not empty.

    A guard whose subject resolves to nothing passes forever. If the regex
    stops matching — the extra renamed, the table reformatted — this is the
    assertion that says so instead of three green tests about nothing.
    """
    assert _alt_extra_imports() == {"best_engine_ai_helper", "wallet_helper"}


@pytest.mark.parametrize(
    "module",
    ["lint_a11y", "sprezzature_accessibility.cli", "alt_from_ollama"],
)
def test_importing_it_loads_nothing_from_the_alt_extra(module: str) -> None:
    """Importing *module* must not drag the drafting half's dependencies in."""
    forbidden = _alt_extra_imports() & _modules_loaded_by(module)
    assert not forbidden, (
        f"importing {module!r} loaded {sorted(forbidden)} from the [alt] extra. "
        "Defer the import to first use, the way `_llm_chat` and `_wallet` do: "
        "the lint is chosen for being installable and runnable with nothing "
        "but click, and a module-level import here ends that quietly."
    )

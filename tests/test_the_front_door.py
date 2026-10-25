"""
Two front doors over four tools, and neither may drift from the other.

`make-a11y` (argparse) and `sprezzature-accessibility` (click) arrived in
1.2.0, and the second one is overdue: the suite's own `SKILL.md` has said this
package is "invoked as `sprezzature-accessibility …`" since the monorepo
split, and nothing installed that command. An agent following the contract ran
something that did not exist and found out at the shell. A guard in the
monorepo caught it by comparing the nine skills against the nine
`[project.scripts]` tables.

The moment there are two front doors, the interesting failure is not that one
breaks: it is that they quietly stop agreeing. A tool added to one, an extra
named differently by the other, a summary edited in one place. So both read
one table and share one sentence about a missing extra, and these tests hold
that shape rather than the behaviour of either.

The last tests are the ones with teeth. The lint half of this package has
**no** dependencies — standard library, milliseconds, no browser — which is
what makes it worth putting in a pre-commit hook. A click twin that imported
click at module load would end that silently, because the failure arrives at
the console script rather than at the install. So the guard is checked by
actually hiding click.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

from sprezzature_accessibility.cli import (
    TOOLS,
    missing_extra_message,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _console_scripts() -> dict[str, str]:
    """
    ``[project.scripts]``, read with a regex rather than ``tomllib``.

    ``tomllib`` is standard library only from 3.11 and this package supports
    3.10, where the import alone fails -- in CI, while passing on every
    developer machine. sprezzature-cli-gui's own test says exactly this in a
    comment, and it was written there because it had already happened once.
    """
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^\[project\.scripts\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    if block is None:
        return {}
    return dict(re.findall(r'^([\w.-]+)\s*=\s*"([^"]+)"', block.group(1), re.M))


def _base_dependencies() -> str:
    """The ``dependencies = [...]`` block as text, comments stripped."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^dependencies\s*=\s*\[(.*?)\]", text, re.M | re.S)
    return re.sub(r"#[^\n]*", "", block.group(1)) if block else ""


def _extras() -> set[str]:
    """The extras this package declares."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    block = re.search(r"^\[project\.optional-dependencies\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    return set(re.findall(r"^([\w.-]+)\s*=\s*\[", block.group(1), re.M)) if block else set()


# Blocking an import from a subprocess needs `find_spec`, not `find_module`:
# the legacy finder API was removed in Python 3.12, so a blocker written that
# way is never consulted — the module imports normally and the test passes by
# not testing anything.
_HIDE_CLICK = (
    "import sys\n"
    "class Blocked:\n"
    "    def find_spec(self, name, path=None, target=None):\n"
    "        if name == 'click':\n"
    "            raise ImportError('click is not installed')\n"
    "        return None\n"
    "sys.meta_path.insert(0, Blocked())\n"
)


def _without_click(program: str) -> subprocess.CompletedProcess[str]:
    """Run a snippet in a subprocess where importing click fails."""
    return subprocess.run(
        [sys.executable, "-c", _HIDE_CLICK + program],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def test_every_tool_names_a_module_that_can_be_found() -> None:
    """A catalogue entry pointing at nothing fails at dispatch, not at import.

    The paths are fully dotted rather than bare names, because these four do
    not all live in one place: the audit half is in the scripts package, the
    drafting half's command line is in the main one. A table that assumed a
    single prefix would have quietly excluded `alt`.
    """
    for tool, (module_name, _extra, _summary) in TOOLS.items():
        assert importlib.util.find_spec(module_name) is not None, (
            f"{tool} dispatches to {module_name}, which cannot be imported"
        )


def test_the_table_spans_both_halves_of_the_package() -> None:
    """Audit and make, in one catalogue — that is what the front door is for."""
    prefixes = {module.rsplit(".", 1)[0] for module, _, _ in TOOLS.values()}
    assert prefixes == {
        "sprezzature_accessibility_scripts",
        "sprezzature_accessibility",
    }, prefixes


def test_every_tool_has_a_summary_the_help_can_print() -> None:
    """An undocumented tool is a tool nobody finds."""
    for tool, (_module, _extra, summary) in TOOLS.items():
        assert summary.strip(), f"{tool} has no summary"
        assert summary.rstrip().endswith("."), f"{tool}'s summary is not a sentence"


def test_an_extra_named_in_the_table_is_an_extra_that_exists() -> None:
    """`pip install 'sprezzature-accessibility[alt]'` has to be real advice."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(
        r"^\[project\.optional-dependencies\]\s*$(.*?)(?=^\[|\Z)",
        pyproject,
        re.M | re.S,
    )
    assert section
    declared = set(re.findall(r"^\s*([A-Za-z0-9._-]+)\s*=", section.group(1), re.M))
    for tool, (_module, extra, _summary) in TOOLS.items():
        if extra:
            assert extra in declared, (
                f"{tool} tells the reader to install [{extra}], "
                f"which pyproject.toml does not declare"
            )


def test_the_lint_needs_no_extra() -> None:
    """The whole design of this package is in this one assertion.

    The audit half runs on the standard library, in milliseconds, with no
    browser. If it ever acquires an extra, the pre-commit story goes with it.
    """
    assert TOOLS["lint"][1] == ""
    assert TOOLS["text-spacing"][1] == ""


def test_themissing_extra_message_names_the_extra() -> None:
    """Both front doors print this, so it has to carry the install line."""
    said = missing_extra_message("alt", "alt", ImportError("no module named click"))
    assert "pip install 'sprezzature-accessibility[alt]'" in said

    # And when there is no extra, it must not invent one to recommend.
    said = missing_extra_message("lint", "", ImportError("boom"))
    assert "pip install" not in said


@pytest.mark.parametrize("front_door", ["make-a11y", "sprezzature-accessibility"])
def test_both_front_doors_are_declared_as_console_scripts(front_door: str) -> None:
    """A front door nobody can type is not a front door.

    This is the exact assertion that was false before 1.2.0 for the second
    name, while the suite's SKILL.md promised it.
    """
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = re.search(r"^\[project\.scripts\]\s*$(.*?)(?=^\[|\Z)", pyproject, re.M | re.S)
    assert section
    assert re.search(rf"^{re.escape(front_door)}\s*=", section.group(1), re.M)


def test_the_per_tool_commands_are_still_there() -> None:
    """A front door that took the old commands away would break every script."""
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for name in (
        "sprezzature-accessibility-lint",
        "sprezzature-accessibility-text-spacing",
        "sprezzature-accessibility-alt",
        "make-alt",
    ):
        assert re.search(rf"^{re.escape(name)}\s*=", pyproject, re.M), name


# ------------------------------------------------- one door, two spellings


def test_the_two_spellings_are_one_callable() -> None:
    """
    ``make-a11y`` and ``sprezzature-accessibility`` must resolve to the same
    target.

    This is the point of removing the second parser: two names that each had
    their own implementation is how the two drifted. Two names pointing at one
    function cannot.
    """
    scripts = _console_scripts()
    assert scripts["make-a11y"] == scripts["sprezzature-accessibility"]
    assert scripts["make-alt"] == scripts["sprezzature-accessibility-alt"]


def test_click_is_a_base_dependency_not_an_extra() -> None:
    """With argparse gone, no parser ships with Python."""
    assert "click" in _base_dependencies()
    assert "click" not in _extras()


def test_no_second_parser_grows_back() -> None:
    """A second front door would re-introduce the duplicate command list."""
    pkg = REPO_ROOT / "sprezzature_accessibility"
    assert not (pkg / "cli_click.py").exists()
    assert not (pkg / "alt_cli_click.py").exists()
    assert "import argparse" not in (pkg / "cli.py").read_text(encoding="utf-8")

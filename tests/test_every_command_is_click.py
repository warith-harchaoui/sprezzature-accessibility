"""
Every command this package installs is click, and nothing it ships imports
argparse.

The suite's decision of 2026-10-25 removed the argparse twins of the front
doors, and the per-tool scripts stayed argparse for nine more days:
``sprezzature-accessibility-lint``, ``-text-spacing`` and ``-mcp`` answered
``--help`` with a lowercase ``usage:`` while the group above them answered
``Usage:``. Two parsers meant two help layouts, two error formats and a shared
factory, ``scripts/_argparse.py``, kept alive for three callers.

Two checks, because they fail apart. A module can import argparse without any
console script reaching it, and a console script can be argparse-shaped
through a library that does the import for it.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The directories this package ships as code: the library and the scripts
#: package (``sprezzature_accessibility_scripts`` on install).
SHIPPED = ("sprezzature_accessibility", "scripts")

_SCRIPTS_SECTION_RE = re.compile(r"^\[project\.scripts\]\s*$(.*?)(?=^\[|\Z)", re.M | re.S)
_SCRIPT_ENTRY_RE = re.compile(r'^\s*([A-Za-z0-9._-]+)\s*=\s*["\']([^"\']+)["\']', re.M)


def _console_scripts() -> dict[str, str]:
    """``{command: "module:attribute"}``, read with a regex (3.10 has no tomllib)."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    section = _SCRIPTS_SECTION_RE.search(text)
    assert section, "pyproject.toml has no [project.scripts] section"
    return dict(_SCRIPT_ENTRY_RE.findall(section.group(1)))


def test_the_package_declares_commands() -> None:
    """An empty table would make the parametrized test below pass on nothing."""
    assert len(_console_scripts()) >= 8


#: Calls the entry point the way the console script does, with ``--help``.
_PROBE = (
    "import importlib, sys\n"
    "module, attr = sys.argv[1].split(':')\n"
    "sys.argv = [sys.argv[2], '--help']\n"
    "sys.exit(getattr(importlib.import_module(module), attr)(['--help']))\n"
)


@pytest.mark.parametrize("command", sorted(_console_scripts()))
def test_help_is_click(command: str) -> None:
    """``--help`` exits 0 and prints click's ``Usage:``, not argparse's ``usage:``."""
    target = _console_scripts()[command]
    done = subprocess.run(
        [sys.executable, "-c", _PROBE, target, command],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=120,
    )
    assert done.returncode == 0, (
        f"`{command} --help` exited {done.returncode}.\n{done.stderr[-800:]}"
    )
    assert done.stdout.startswith("Usage:"), (
        f"`{command} --help` does not answer with click's usage line; it starts "
        f"with {done.stdout[:60]!r}. Every command of the suite is click."
    )


def _imports_argparse(path: Path) -> bool:
    """Whether *path* imports argparse anywhere, at module level or inside a def."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name.split(".")[0] == "argparse" for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "argparse":
            return True
    return False


def test_no_shipped_module_imports_argparse() -> None:
    """Read from the source, so a deferred import inside ``main`` counts too."""
    sources = [
        path
        for folder in SHIPPED
        for path in sorted((REPO_ROOT / folder).rglob("*.py"))
        if "__pycache__" not in path.parts
    ]
    assert sources, "no Python sources found: the scan would pass on nothing"
    offenders = [str(p.relative_to(REPO_ROOT)) for p in sources if _imports_argparse(p)]
    assert not offenders, (
        f"{offenders} import argparse. The suite's commands are click only: use "
        f"`sprezzature_command` and `run_command` from scripts/_click.py."
    )

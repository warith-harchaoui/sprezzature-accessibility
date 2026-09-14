"""
The version is written in two places and read in a third, and nothing tied
them together.

``__version__`` is what ``api.py`` hands FastAPI, so it reaches
``/openapi.json`` and the headline an MCP host displays; ``pyproject.toml`` is
what pip installs. In ``sprezzature-figures`` those two drifted and the API
advertised 2.0.0 through the whole 2.1.0 release — a defect no test could see,
because neither number is used by any code path a test exercises.

The CHANGELOG is the third: a release whose top section names an older version
ships undocumented changes.

Read with a regex rather than ``tomllib``, which is stdlib only from 3.11 while
this package supports 3.10.

Author
------
Warith HARCHAOUI <warith.harchaoui@gmail.com>
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from sprezzature_accessibility import __version__

REPO_ROOT = Path(__file__).resolve().parent.parent

_PYPROJECT_VERSION_RE = re.compile(r'^\s*version\s*=\s*["\']([\d.]+)["\']', re.MULTILINE)
_RELEASE_HEADING_RE = re.compile(r"^##\s+\[?v?([\d.]+)\]?", re.MULTILINE)


def _pyproject_version() -> str:
    """The ``project.version`` pip installs, straight from pyproject.toml."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = _PYPROJECT_VERSION_RE.search(text)
    assert match, "pyproject.toml declares no project version"
    return match.group(1)


def test_package_version_matches_pyproject() -> None:
    """``__version__`` is what the surfaces advertise; pyproject is what pip installs."""
    declared = _pyproject_version()
    assert __version__ == declared, (
        f"version drift: sprezzature_accessibility.__version__ is {__version__!r} but "
        f"pyproject.toml declares {declared!r}."
    )


def test_changelog_leads_with_the_current_version() -> None:
    """The top release section of the CHANGELOG names the version being shipped."""
    text = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    headings = _RELEASE_HEADING_RE.findall(text)
    assert headings, "CHANGELOG.md has no release headings"
    assert headings[0] == __version__, (
        f"CHANGELOG.md leads with {headings[0]}, but the package is {__version__}. "
        "A release whose top section is an older version ships undocumented changes."
    )


#: Files whose prose tells a reader how many rules the linter has.
_COUNT_CLAIMING_FILES = (
    "README.md",
    "LISEZMOI.md",
    "references/lint-rules.md",
    "scripts/lint_a11y.py",
)

#: Digits and the written-out forms this project actually uses, next to the
#: word "rule" / "règle" in either order.
_WORDS = {
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty-one": 21,
    "quatorze": 14, "quinze": 15, "seize": 16, "dix-sept": 17,
    "dix-huit": 18, "dix-neuf": 19, "vingt": 20, "vingt-et-une": 21,
}
_CLAIM_RE = re.compile(
    r"\b(\d{1,3}|" + "|".join(_WORDS) + r")[\s-]+(?:rules?|règles?)\b"
    r"|\b(?:rules?|règles?)[\s-]+(\d{1,3})\b",
    re.IGNORECASE,
)


def _claimed_counts(text: str) -> set[int]:
    """Every rule count the prose states, digits and words alike."""
    found: set[int] = set()
    for match in _CLAIM_RE.finditer(text):
        token = (match.group(1) or match.group(2) or "").lower()
        if token.isdigit():
            found.add(int(token))
        elif token in _WORDS:
            found.add(_WORDS[token])
    return found


@pytest.mark.parametrize("relative_path", _COUNT_CLAIMING_FILES)
def test_quoted_rule_count_matches_the_linter(relative_path: str) -> None:
    """
    A rule count written at a reader equals ``len(ALL_RULES)``.

    The linter grew to twenty rules — the five time-based-media checks among
    them — while every document still said fifteen. Nobody reading the README
    could learn that their `<video>` was being checked at all, which is the
    expensive half of the mistake: not a wrong number, an invisible feature.

    The six auto-fixers are a genuinely different count and are excluded, so
    "6 rules" phrasings are matched against ``RULE_FIXERS`` instead.
    """
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lint_a11y import ALL_RULES, RULE_FIXERS

    text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
    legitimate = {len(ALL_RULES), len(RULE_FIXERS)}
    wrong = sorted(_claimed_counts(text) - legitimate)
    assert not wrong, (
        f"{relative_path} tells the reader the linter has {wrong} rule(s), but "
        f"ALL_RULES holds {len(ALL_RULES)} (and RULE_FIXERS {len(RULE_FIXERS)}). "
        f"Adding a rule without touching this file is how the count went stale."
    )

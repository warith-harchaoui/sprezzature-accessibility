"""
The YAML-backed prompts, checked without talking to a model.

Every prompt this package sends is assembled from a YAML file under
``scripts/prompts/``, never from a string literal buried in the code. Two
things are decidable without a model, and both matter: that each file loads
through ``_prompts.load_prompt`` (PyYAML is optional, so the stdlib fallback
has to work), and that the assembled prompt still carries the instruction the
W3C decision tree depends on for that image purpose.

Moved here from the monorepo when this package was extracted, so the prompts
and the code that assembles them live in one place and a change to either is
caught by a test sitting beside it.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMPTS = REPO_ROOT / "scripts" / "prompts"

#: Each shipped prompt, with a phrase the script's behaviour depends on.
#: Declared once and used twice: to assert the contract, and to assert that
#: the table has not drifted behind the folder.
CONTRACTS: tuple[tuple[str, str], ...] = (
    ("alt_short_default", "Reply with the alt text only"),
    ("alt_short_informative", "informative image"),
    ("alt_short_functional", "action or destination"),
    ("alt_short_text", "verbatim"),
    ("alt_short_complex", "complex image"),
    ("alt_short_group", "group of images"),
    ("alt_long_default", "long-form description"),
    ("alt_long_complex", "Markdown"),
    ("alt_long_group", "group of related images"),
)


@pytest.mark.parametrize("name, must_contain", CONTRACTS)
def test_prompt_yaml_loads(name: str, must_contain: str) -> None:
    """Each prompt file reads, and still says what the script relies on."""
    from _prompts import load_prompt  # type: ignore

    data = load_prompt(name, prompts_dir=PROMPTS)
    assert "template" in data
    haystack = data.get("output_contract", "") + data["template"] + data.get("task", "")
    assert must_contain in haystack, f"{name}.yaml no longer contains {must_contain!r}"


def test_every_shipped_prompt_is_covered() -> None:
    """
    The table above must not drift behind the folder.

    A prompt file nobody asserts on is one that can be emptied without a test
    noticing — and an empty prompt still produces output, just worse output,
    which is the regression that reaches a reader rather than a build.
    """
    shipped = {path.stem for path in PROMPTS.glob("*.yaml")}
    covered = {name for name, _ in CONTRACTS}
    assert shipped == covered, (
        f"prompt files with no assertion: {sorted(shipped - covered)}; "
        f"assertions with no file: {sorted(covered - shipped)}"
    )


@pytest.mark.parametrize(
    "kind, must_contain",
    [
        ("informative", "informative image"),
        ("functional", "link or button"),
        ("text", "verbatim"),
        ("complex", "complex image"),
        ("group", "group of images"),
        ("decorative", "Write alt text for this image"),  # falls through to default
    ],
)
def test_alt_short_prompt_per_kind(kind: str, must_contain: str) -> None:
    from alt_from_ollama import prompt_for  # type: ignore

    out = prompt_for(kind=kind, lang="en", context="A dashboard tile")
    assert "Write the alt text in English." in out
    assert must_contain in out


def test_alt_short_text_kind_skips_base_rules() -> None:
    """The `text` purpose extracts verbatim text; generic rules don't apply."""
    from alt_from_ollama import prompt_for  # type: ignore

    out = prompt_for(kind="text", lang="en", context="")
    # The "do not start with image of" rule belongs to the generic kinds.
    assert "Do not start with 'image of'" not in out
    assert "verbatim" in out


@pytest.mark.parametrize(
    "kind, must_contain",
    [
        ("complex", "chart type / diagram type"),
        ("group", "group of related images"),
        ("other", "long-form description"),  # falls through to default
    ],
)
def test_alt_long_prompt_per_kind(kind: str, must_contain: str) -> None:
    from alt_from_ollama import long_prompt_for  # type: ignore

    out = long_prompt_for(kind=kind, lang="en", context="")
    assert must_contain in out


def test_alt_prompt_substitutes_context_when_supplied() -> None:
    from alt_from_ollama import prompt_for  # type: ignore

    out = prompt_for(kind="informative", lang="en", context="Hero image of the homepage")
    assert "Page context: Hero image of the homepage." in out


def test_alt_prompt_omits_context_block_when_empty() -> None:
    from alt_from_ollama import prompt_for  # type: ignore

    out = prompt_for(kind="informative", lang="en", context="")
    assert "Page context:" not in out

"""
One authorized model, and no knob to change it.

``qwen3-vl:8b`` is not a default to be overridden on a whim. The per-purpose
prompts, the length budget and the post-processing were all tuned against it,
so swapping the model silently changes what the W3C decision tree produces —
and the caller has no way to tell, because a different model still returns a
plausible sentence.

That is why the model is fixed rather than configurable. ``OLLAMA_MODEL``
survives as a bare environment seam for tests; it is deliberately not a
documented user option, and no command line may expose a ``--model`` flag.

These assertions used to live in the monorepo's ``test_single_llm.py``, which
read this package's scripts across the folder boundary. They moved here with
the code: an assertion about a file belongs in the repository that can still
see it.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

#: The scripts that hard-code a default model constant.
DECLARERS = (
    ROOT / "scripts" / "alt_from_ollama.py",
    ROOT / "scripts" / "install_alt_ai.py",
)

#: Every module a user can reach, including the two command lines. A flag
#: added to either parser would be just as user-facing as one in the engine.
REACHABLE = DECLARERS + (
    ROOT / "sprezzature_accessibility" / "alt_cli.py",
    ROOT / "sprezzature_accessibility" / "alt_cli_click.py",
    ROOT / "sprezzature_accessibility" / "api.py",
)

#: An option *definition* that would put the model on the command line —
#: click's ``@click.option("--model"…)`` or argparse's
#: ``add_argument("--model"…)``. Prose mentions and internal ``model=``
#: keyword arguments are fine; a defined flag is the violation.
MODEL_FLAG = re.compile(r'"--(?:model|ai-hints-model)"')


@pytest.mark.parametrize("script", DECLARERS, ids=lambda p: p.name)
def test_the_declared_default_is_the_authorized_model(script: Path) -> None:
    """Each declarer names a ``qwen3-vl:`` tag, not some other family."""
    text = script.read_text(encoding="utf-8")
    assert '"qwen3-vl:' in text, (
        f"{script.name} must declare a qwen3-vl: tag as its default model"
    )


@pytest.mark.parametrize("module", REACHABLE, ids=lambda p: p.name)
def test_no_surface_exposes_a_model_flag(module: Path) -> None:
    """
    No command line may let a caller pick the model.

    Checked across both parsers and the HTTP surface rather than the engine
    alone: the whole point of having four surfaces over one engine is that
    they agree, and a knob added to one of them is a knob the others do not
    have.
    """
    text = module.read_text(encoding="utf-8")
    assert not MODEL_FLAG.search(text), (
        f"{module.name} defines a user-facing model flag. The model is fixed "
        f"at qwen3-vl:8b — the prompts are tuned to it, and a different model "
        f"returns a plausible sentence that silently means something else."
    )


def test_the_library_publishes_the_model_it_will_use() -> None:
    """
    ``DEFAULT_BASE`` is exported, so a caller can see what answered.

    A fixed model that the caller cannot name is worse than a configurable
    one: it makes the output unattributable.
    """
    import sprezzature_accessibility

    assert sprezzature_accessibility.DEFAULT_BASE.startswith("qwen3-vl:")
    assert "DEFAULT_BASE" in sprezzature_accessibility.__all__

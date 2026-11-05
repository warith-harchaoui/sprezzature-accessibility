"""
``--resize`` has to change the bytes the model receives.

Until 2026-11-04 Pillow was declared nowhere in ``pyproject.toml``, so on a
default install the flag was accepted, documented with a default of 1024, and
did nothing: ``maybe_resize`` found no Pillow and forwarded the original bytes.
Nothing failed, which is why nothing caught it. The existing tests covered the
two branches that return the input unchanged and not the one that resizes.

Two checks. The first asks the manifest, since the bug was an undeclared
dependency. The second drives the command line with a generated image and
reads the size of what reached the model, which is the only place the flag is
visible.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_pillow_is_a_base_dependency() -> None:
    """Read with a regex, not ``tomllib``, which 3.10 does not ship."""
    text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    base = re.search(r"^dependencies = \[(.*?)^\]", text, re.MULTILINE | re.DOTALL)
    assert base, "no `dependencies = [...]` in pyproject.toml"
    names = {n.lower() for n in re.findall(r'^\s*"([A-Za-z0-9._-]+)', base.group(1), re.MULTILINE)}
    assert "pillow" in names, (
        "Pillow is not in the base dependencies, so `--resize` silently sends "
        "the original image on a default install."
    )


def test_the_flag_resizes_what_the_model_receives(tmp_path: Path) -> None:
    """A 400x200 image with ``--resize 64`` reaches the model as 64x32."""
    image_mod = pytest.importorskip("PIL.Image")

    src = tmp_path / "wide.png"
    image_mod.new("RGB", (400, 200), (200, 40, 40)).save(src, format="PNG")

    from sprezzature_accessibility import alt_cli

    # The engine module the command line actually calls. A bare
    # ``import alt_from_ollama`` would be a second module object, and patching
    # it would leave the real call untouched.
    engine = sys.modules[alt_cli.run.__module__]
    assert engine.HAVE_PILLOW, "Pillow imports here, so the engine must see it"

    sent: list[bytes] = []

    def fake_chat(prompt: str, *, images: list[bytes], model: str, engine: object) -> str:
        sent.extend(images)
        return "A red rectangle"

    with patch.object(engine, "_llm_chat", side_effect=fake_chat):
        code = alt_cli.main(["--resize", "64", "--lang", "en", "--no-cache", str(src)])

    assert code == 0
    assert len(sent) == 1, f"expected one model call, got {len(sent)}"
    with image_mod.open(io.BytesIO(sent[0])) as received:
        assert received.size == (64, 32), (
            f"the model received a {received.size} image; `--resize 64` "
            "should have capped the longest edge at 64 px"
        )

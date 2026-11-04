"""
The HTTP schema states the engine's alt-text limit, not a copy of it.

``api.py`` falls back to its own ``DEFAULT_BASE`` and ``MAX_CHARS`` when the
drafting engine cannot be imported. That copy said 125 while the engine cut
at 150, so a broken install would have published a limit nothing enforced.
The fallback now reads the engine's own literals; this checks it agrees with
the imported values.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import alt_from_ollama  # noqa: E402

from sprezzature_accessibility import api  # noqa: E402


def test_the_fallback_reads_the_engine_constants() -> None:
    assert api._engine_constants() == (
        alt_from_ollama.DEFAULT_BASE,
        alt_from_ollama.MAX_CHARS,
    )


def test_the_schema_publishes_the_engine_limit() -> None:
    description = api.AltResponse.model_fields["alt"].description or ""
    assert str(alt_from_ollama.MAX_CHARS) in description

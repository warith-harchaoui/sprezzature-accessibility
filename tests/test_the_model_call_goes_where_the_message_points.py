"""
The server ``OLLAMA_URL`` names is the server the model call reaches.

The drafter names ``OLLAMA_URL`` when it cannot reach the model ("Cannot reach
Ollama at …"), and the compose file sets it to the ``ollama`` service. Until
2026-11-05 the call itself went through ``best_engine_ai_helper.llm.chat``
with no endpoint, so it reached whatever best-engine-ai-helper was configured
with (``SPREZZATURE_LLM_BASE_URL``, localhost by default). In the compose
stack that is the API container itself: the draft failed there and the message
blamed a server nobody had called.

These tests put a recording ``chat`` where ``_llm_chat`` imports it from, so
they need no server and no model, and cannot reach one if one is running. They
go through the command line's own module object, not ``import
alt_from_ollama``, which would be a second copy whose ``OLLAMA_URL`` the real
call never reads.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any

import pytest

URL = "http://ollama.example:11434"
MODEL = "qwen3-vl:8b"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "images" / "chart-bar.png"


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch) -> Any:
    """The drafting module the command line calls, pointed at :data:`URL`."""
    from sprezzature_accessibility import alt_cli

    module = sys.modules[alt_cli.run.__module__]
    monkeypatch.setattr(module, "OLLAMA_URL", URL)
    monkeypatch.setattr(module, "NO_CACHE", True)
    return module


def _stub_chat(monkeypatch: pytest.MonkeyPatch, reply: str | Exception) -> list[dict[str, Any]]:
    """Put a recording ``chat`` where ``_llm_chat`` imports it from.

    A stand-in module rather than a patched attribute, so the import inside
    ``_llm_chat`` is exercised as it is in production, and nothing here
    depends on best-engine-ai-helper being importable.
    """
    calls: list[dict[str, Any]] = []

    def chat(prompt: str, **kwargs: Any) -> str:
        calls.append({"prompt": prompt, **kwargs})
        if isinstance(reply, Exception):
            raise reply
        return reply

    package = types.ModuleType("best_engine_ai_helper")
    llm = types.ModuleType("best_engine_ai_helper.llm")
    llm.chat = chat  # type: ignore[attr-defined]
    package.llm = llm  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "best_engine_ai_helper", package)
    monkeypatch.setitem(sys.modules, "best_engine_ai_helper.llm", llm)
    return calls


def _assert_reaches(call: dict[str, Any]) -> None:
    descriptor = call.get("engine")
    assert isinstance(descriptor, dict), (
        "chat() was called without an engine descriptor, so it goes to "
        "best-engine-ai-helper's own endpoint and not to OLLAMA_URL"
    )
    assert descriptor["backend"] == "ollama"
    assert descriptor["base_url"] == URL
    # Every call here carries an image, and chat() reads the `vlm` section
    # for those; `llm` alone raises KeyError before any request is made.
    assert call["images"], "the drafter's calls all carry the image"
    assert descriptor["vlm"]["model"] == MODEL
    assert call["model"] == MODEL


def test_the_short_alt_calls_the_url_it_names(engine: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_chat(monkeypatch, "Quarterly revenue, rising each quarter")
    out = engine.describe(str(FIXTURE), kind="informative", lang="en", model=MODEL)
    assert out
    assert len(calls) == 1
    _assert_reaches(calls[0])


def test_the_long_description_calls_the_url_it_names(engine: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_chat(monkeypatch, "- Q1: 10\n- Q2: 12")
    engine.describe_long(str(FIXTURE), lang="en", model=MODEL)
    assert len(calls) == 1
    _assert_reaches(calls[0])


def test_the_error_names_the_url_that_was_called(
    engine: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The message and the call read the same address, at the same moment."""
    calls = _stub_chat(monkeypatch, RuntimeError("connection refused"))
    with pytest.raises(SystemExit) as excinfo:
        engine.describe(str(FIXTURE), kind="informative", lang="en", model=MODEL)
    assert excinfo.value.code == engine.EXIT_MODEL_UNREACHABLE
    assert len(calls) == 1
    _assert_reaches(calls[0])
    assert f"Cannot reach Ollama at {URL}" in capsys.readouterr().err


def test_the_descriptor_resolves_for_an_image_call() -> None:
    """The real resolver, not the stub, accepts the descriptor for a VLM call.

    The stub above records whatever it is given; this is the half that says
    best-engine-ai-helper reads it as an Ollama call to :data:`URL`.
    """
    resolver = pytest.importorskip("best_engine_ai_helper.engine")
    from sprezzature_accessibility_scripts.alt_from_ollama import ollama_engine

    descriptor = ollama_engine(URL, MODEL)
    assert resolver.model_for(descriptor, "vlm") == ("ollama", URL, MODEL)
    assert resolver.model_for(descriptor, "llm") == ("ollama", URL, MODEL)

"""
Shared pytest configuration.

Three jobs, each of which this suite stops being honest without.

1. **Import path.** ``scripts/`` goes on ``sys.path`` so the test modules can
   ``import alt_from_ollama`` directly, mirroring how the scripts import each
   other at run time: they insert their own folder and import siblings by bare
   name. Installed, that folder is ``sprezzature_accessibility_scripts``; from a
   clone it is ``scripts/``, and these tests have to work from a clone.
2. **Cache isolation**, so a run neither pollutes nor is polluted by the
   developer's real cache at ``~/.cache/sprezzature-skill/``.
3. **Keeping the content-safety scan out of unit tests that mock the
   transport** — see :func:`no_content_scan`, which is the one with teeth.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path, monkeypatch):
    """Redirect the on-disk cache to a per-test temp directory."""
    monkeypatch.setenv("SPREZZATURE_CACHE_DIR", str(tmp_path / "sprezzature-skill"))
    # The toggle survives across tests if a module reads it at import time;
    # make sure each test sees the same default.
    monkeypatch.delenv("SPREZZATURE_NO_CACHE", raising=False)


@pytest.fixture(autouse=True)
def no_content_scan(monkeypatch):
    """
    Keep the content-safety scan out of unit tests that mock the transport.

    ``lint_a11y`` or The drafting half calls ``best_engine_ai_helper.llm.chat``, which since
    1.4 scans every prompt and response through an NSFW classifier before the
    request leaves — on by default for local engines too. The classifier is an
    optional extra (``[filtered]``), so a bare install falls back to a keyword
    heuristic and nothing happens here.

    But on a machine where ``transformers`` is installed for some other
    reason, the scan loads a 270 MB model from HuggingFace, and these tests go
    from "the Ollama call is mocked" to "the suite downloads a model and needs
    the network". That is a CI job that fails for a reason nothing in this
    repository caused, and a local run that takes seven seconds where it
    should take milliseconds.

    The scan belongs to the dependency and is tested there; nothing here
    asserts on it.
    """
    try:
        from best_engine_ai_helper import safety
    except ImportError:  # the dependency is absent — nothing to neutralise
        return
    for name in ("check_text", "check_image"):
        if hasattr(safety, name):
            monkeypatch.setattr(safety, name, lambda *a, **k: None)

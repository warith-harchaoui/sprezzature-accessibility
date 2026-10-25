"""
The loop this package exists to close: the lint finds it, the model writes it.

``lint_a11y`` has always reported ``img-missing-alt`` and stopped. Its fixer
table said why, in a comment: the rules absent from it need "a content
decision the linter cannot make for the user". Merging the drafting half in
removes that limit — but only if the draft is actually informed by the page.

That is what these tests hold. A model shown ``photo.jpg`` alone writes *a*
description. The W3C decision tree asks what an image is **doing** on the
page, which is a question about the page. So the assertion that matters is
not "alt appeared" but "the text around the image reached the model", and the
tests below read the arguments the engine was called with rather than trusting
that the wiring looks right.

No model runs here: ``describe`` is stubbed. What is under test is the loop,
not the quality of its prose.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fill_alt  # noqa: E402

PAGE = """\
<!doctype html>
<html lang="en">
<body>
<h2>The Serre-Ponçon reservoir in July</h2>
<p>Usable capacity has fallen to 63 percent, eleven points below the
ten-year median for the date.</p>
<img src="lake.png" width="800">
<p>The operator expects the shortfall to persist into September.</p>
</body>
</html>
"""


@pytest.fixture
def page(tmp_path: Path) -> Path:
    """A document with one image that has no alt, and prose around it."""
    (tmp_path / "lake.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    path = tmp_path / "report.html"
    path.write_text(PAGE, encoding="utf-8")
    return path


@pytest.fixture
def spy(monkeypatch):
    """Stand in for the model and record what it was asked."""
    calls: list[dict] = []

    def fake_describe(src, **kwargs):
        calls.append({"src": src, **kwargs})
        return "Serre-Ponçon at 63 percent of usable capacity in July"

    import alt_from_ollama

    monkeypatch.setattr(alt_from_ollama, "describe", fake_describe)
    monkeypatch.setattr(alt_from_ollama, "detect_lang", lambda: "en")
    return calls


def test_the_lint_finds_what_the_model_then_fills(page: Path, spy) -> None:
    """End to end: a finding becomes an attribute on disk."""
    drafts, unreachable = fill_alt.fill_missing_alt(page)

    assert len(drafts) == 1, f"expected one draft, got {drafts}"
    assert not unreachable
    assert 'alt="Serre-Ponçon at 63 percent of usable capacity in July"' in (
        page.read_text(encoding="utf-8")
    )


def test_the_page_text_reaches_the_model(page: Path, spy) -> None:
    """
    The assertion the whole merge is for.

    Without this, the drafter is the standalone tool it used to be, called
    from a new place. With it, the alt is about *this* page: the heading above
    the image and the sentence beside it are in the prompt.
    """
    fill_alt.fill_missing_alt(page)

    context = spy[0]["context"]
    assert "Serre-Ponçon" in context, (
        f"the heading above the image never reached the model; context was "
        f"{context!r}"
    )
    assert "63 percent" in context or "usable capacity" in context, (
        "the paragraph beside the image never reached the model"
    )


def test_the_document_vocabulary_reaches_the_model(page: Path, spy) -> None:
    """
    Proper nouns from the page bias the draft.

    This is what keeps the result from saying "a lake": the model is handed
    the spellings the document itself uses.
    """
    fill_alt.fill_missing_alt(page)

    terms = spy[0]["vocabulary"]
    assert terms, "no vocabulary was mined from the document at all"
    assert any("Serre" in term for term in terms), (
        f"the document's own proper nouns are missing from the vocabulary "
        f"hint: {terms}"
    )


def test_a_remote_image_is_left_alone(tmp_path: Path, spy) -> None:
    """
    Nothing is fetched from the network.

    This runs over a developer's working tree. Silently reaching out to
    whatever a page happens to link to is not something a lint should do, so a
    remote source is reported as unreachable rather than downloaded.
    """
    path = tmp_path / "remote.html"
    path.write_text(
        '<html lang="en"><body><img src="https://example.com/a.png"></body></html>',
        encoding="utf-8",
    )
    drafts, unreachable = fill_alt.fill_missing_alt(path)

    assert drafts == []
    assert len(unreachable) == 1
    assert spy == [], "the model was called for an image that was never read"


def test_a_dry_run_writes_nothing(page: Path, spy) -> None:
    """Preview mode drafts and reports without touching the file."""
    before = page.read_text(encoding="utf-8")
    drafts, _ = fill_alt.fill_missing_alt(page, dry_run=True)

    assert len(drafts) == 1
    assert page.read_text(encoding="utf-8") == before


def test_the_alt_is_escaped(page: Path, monkeypatch) -> None:
    """
    A draft containing a quote must not break the tag it lands in.

    The model writes prose, and prose contains punctuation. Splicing it into
    an attribute without escaping would turn one image into malformed markup —
    an accessibility tool making the page worse.
    """
    import alt_from_ollama

    monkeypatch.setattr(
        alt_from_ollama, "describe",
        lambda src, **kw: 'A sign reading "No swimming" & a jetty',
    )
    monkeypatch.setattr(alt_from_ollama, "detect_lang", lambda: "en")

    fill_alt.fill_missing_alt(page)
    text = page.read_text(encoding="utf-8")

    assert "&quot;No swimming&quot;" in text
    assert "&amp;" in text
    # and the document still parses into exactly one img with an alt
    from lint_a11y import lint_file

    assert not [f for f in lint_file(page, set()) if f.rule == "img-missing-alt"]


def test_an_already_described_image_is_not_redrafted(page: Path, spy) -> None:
    """
    Idempotent: running twice calls the model once.

    A drafting pass that re-ran on every invocation would cost seconds per
    image and overwrite the wording a human had just corrected.
    """
    fill_alt.fill_missing_alt(page)
    fill_alt.fill_missing_alt(page)

    assert len(spy) == 1, f"the model was called {len(spy)} times, not once"

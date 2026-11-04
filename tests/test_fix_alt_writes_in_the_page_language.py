"""
``--fix-alt`` writes alt text in the language of the page, not of the machine.

Found on 2026-11-04: without ``--alt-lang``, ``fill_missing_alt`` asked only
the environment locale (``ALT_LANG``, ``LC_ALL``, ``LANG``), while the flag's
help promised detection from the document. A French page linted on an
English machine was given English alt text, which a screen reader then
pronounced with French phonetics, because the page's ``lang`` said French.

The order under test: ``<html lang>`` first, detection on the page text
second, the environment locale last. ``describe`` is stubbed: what is under
test is the language the model is *asked* for.

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

FRENCH_PROSE = (
    "<p>Le barrage de Serre-Ponçon retient le plus grand lac artificiel de "
    "France. Son niveau a baissé tout au long de l'été, et les communes "
    "riveraines s'inquiètent pour la saison prochaine.</p>"
)


@pytest.fixture
def asked(monkeypatch) -> list[str]:
    """Record the language each draft was requested in; the machine is English."""
    import alt_from_ollama

    langs: list[str] = []

    def fake_describe(src, **kwargs):
        langs.append(kwargs["lang"])
        return "Le lac de Serre-Ponçon"

    monkeypatch.setattr(alt_from_ollama, "describe", fake_describe)
    monkeypatch.setattr(alt_from_ollama, "detect_lang", lambda: "en")
    return langs


def _page(tmp_path: Path, html_open: str, body: str) -> Path:
    (tmp_path / "lac.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    path = tmp_path / "page.html"
    path.write_text(
        f'{html_open}<body>\n{body}\n<img src="lac.png">\n</body></html>\n',
        encoding="utf-8",
    )
    return path


def test_the_declared_lang_wins_over_the_machine(tmp_path: Path, asked) -> None:
    """``<html lang="fr-FR">`` means French drafts on an English machine."""
    fill_alt.fill_missing_alt(_page(tmp_path, '<html lang="fr-FR">', "<p>x</p>"))
    assert asked == ["fr"]


def test_the_page_text_decides_when_nothing_is_declared(tmp_path: Path, asked) -> None:
    """No ``lang`` attribute: the visible French prose decides."""
    pytest.importorskip("langdetect")
    fill_alt.fill_missing_alt(_page(tmp_path, "<html>", FRENCH_PROSE))
    assert asked == ["fr"]


def test_the_locale_is_the_last_resort(tmp_path: Path, asked) -> None:
    """No declaration and too little text: the environment answers."""
    fill_alt.fill_missing_alt(_page(tmp_path, "<html>", "<p>ok</p>"))
    assert asked == ["en"]


def test_an_explicit_alt_lang_still_wins(tmp_path: Path, asked) -> None:
    """``--alt-lang`` overrides the page, as it always did."""
    fill_alt.fill_missing_alt(
        _page(tmp_path, '<html lang="fr">', FRENCH_PROSE), lang="de"
    )
    assert asked == ["de"]

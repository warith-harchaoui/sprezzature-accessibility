"""
A repair changes the element it was asked about, and nothing else in the file.

Found on 2026-11-08, by running the commands on ordinary pages rather than the
fixtures. Each test here failed before the fix:

- ``--fix`` wrote back what a lossy read had left, so a Latin-1 page lost every
  accented letter even when no fix applied, and a CRLF file came out LF.
- A finding carries a line and no column, and the fixers edited the first
  matching attribute on that line. On a minified page, that belonged to some
  other element: the decorative icon beside the control lost its
  ``aria-hidden``, and the guard landed on the wrong ``class``.
- ``--fix-alt`` wrote into the first ``<img`` of the line, whatever it was.

The rest is the same family on the audit side, a false verdict: a name written
as a character reference or given by ``aria-labelledby`` was reported missing,
and a path with a typo in it exited 0.

``describe`` is stubbed: what is under test is where the text lands.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fill_alt  # noqa: E402
import lint_a11y  # noqa: E402

from sprezzature_accessibility import api  # noqa: E402
from sprezzature_accessibility.alt_cli import main as alt_main  # noqa: E402


def _rules(html: str) -> list[str]:
    return [f.rule for f in lint_a11y.lint_html(html)]


def _fix(tmp_path: Path, content: bytes) -> tuple[bytes, list[lint_a11y.Finding]]:
    page = tmp_path / "page.html"
    page.write_bytes(content)
    _, _, remaining = lint_a11y.fix_file(page, set())
    return page.read_bytes(), remaining


# ── The audit: a name is a name, and a wrong path is not a clean run ────────


@pytest.mark.parametrize("label", ["&times;", "&#215;", "&#xD7;", "Caf&eacute;"])
def test_a_character_reference_is_a_name(label: str) -> None:
    assert "button-empty" not in _rules(f"<button>{label}</button>")


def test_a_non_breaking_space_is_still_no_name() -> None:
    assert "button-empty" in _rules("<button>&nbsp;</button>")


def test_a_close_label_spelled_with_a_reference_counts() -> None:
    html = "<dialog><button>Schlie&szlig;en</button></dialog>"
    assert "dialog-missing-close" not in _rules(html)


@pytest.mark.parametrize(
    ("html", "rule"),
    [
        ('<button aria-labelledby="t"></button>', "button-empty"),
        ('<a href="/" aria-labelledby="t"></a>', "a-empty"),
        ('<input aria-labelledby="t">', "input-missing-label"),
    ],
)
def test_aria_labelledby_names_an_element(html: str, rule: str) -> None:
    assert rule not in _rules(html)


def test_an_id_does_not_shadow_the_words_of_a_close_button() -> None:
    html = '<dialog><button aria-labelledby="t">Close</button></dialog>'
    assert "dialog-missing-close" not in _rules(html)


def test_a_path_that_does_not_exist_is_a_usage_error(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as stopped:
        lint_a11y.main([str(tmp_path / "typo")])
    assert stopped.value.code == 2


# ── The bytes of the file ───────────────────────────────────────────────────


def test_a_latin1_page_keeps_its_accents_when_no_fix_applies(tmp_path: Path) -> None:
    source = '<html lang="fr"><p>caf\xe9 \xe0 No\xebl</p></html>\n'.encode("latin-1")
    assert _fix(tmp_path, source)[0] == source


def test_a_latin1_page_keeps_its_accents_when_a_fix_applies(tmp_path: Path) -> None:
    source = '<html lang="fr"><p>caf\xe9</p><a href="/" tabindex="3">x</a></html>\n'
    after, remaining = _fix(tmp_path, source.encode("latin-1"))
    assert after == source.replace('tabindex="3"', 'tabindex="0"').encode("latin-1")
    assert remaining == []


def test_crlf_line_endings_survive(tmp_path: Path) -> None:
    source = b'<html lang="fr">\r\n<a href="/" tabindex="3">x</a>\r\n</html>\r\n'
    after, _ = _fix(tmp_path, source)
    assert after == source.replace(b'tabindex="3"', b'tabindex="0"')


def test_a_form_feed_is_not_a_line(tmp_path: Path) -> None:
    source = b'<html lang="fr">\x0c<p>x</p>\n<a href="/" tabindex="3">x</a>\n</html>'
    after, remaining = _fix(tmp_path, source)
    assert after == source.replace(b'tabindex="3"', b'tabindex="0"')
    assert remaining == []


def test_a_file_with_nothing_to_fix_is_not_written(tmp_path: Path) -> None:
    page = tmp_path / "page.html"
    page.write_text('<html lang="fr"><p>ok</p></html>\n', encoding="utf-8")
    page.chmod(0o444)  # a write would raise
    lint_a11y.fix_file(page, set())


# ── The element on the line ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (
            '<span aria-hidden="true">*</span><button aria-hidden="true">ok</button>',
            '<span aria-hidden="true">*</span><button>ok</button>',
        ),
        (
            '<a href="/" tabindex="-1" aria-hidden="true">a</a><a href="/b" aria-hidden="true">b</a>',
            '<a href="/" tabindex="-1" aria-hidden="true">a</a><a href="/b">b</a>',
        ),
        (
            '<span aria-hidden="true">*</span><img alt="" aria-hidden="true">',
            '<span aria-hidden="true">*</span><img alt="">',
        ),
        (
            '<div class="p-1"><span class="animate-spin">z</span></div>',
            '<div class="p-1"><span class="animate-spin motion-reduce:transform-none">z</span></div>',
        ),
        (
            '<div class="tracking-tight"><p class="tracking-tight m-1">z</p></div>',
            '<div class="tracking-tight"><p class="m-1">z</p></div>',
        ),
    ],
)
def test_the_fixer_edits_the_element_the_finding_is_about(
    tmp_path: Path, before: str, after: str
) -> None:
    shell = '<html lang="en">\n{}\n</html>\n'
    fixed, remaining = _fix(tmp_path, shell.format(before).encode())
    assert fixed.decode() == shell.format(after)
    assert remaining == []


def test_every_offender_on_a_line_is_fixed(tmp_path: Path) -> None:
    source = '<html lang="en">\n' + '<button aria-hidden="true">a</button>' * 5 + "\n</html>\n"
    fixed, remaining = _fix(tmp_path, source.encode())
    assert b"aria-hidden" not in fixed
    assert remaining == []


def test_a_greater_than_inside_a_value_does_not_end_the_tag(tmp_path: Path) -> None:
    source = '<html lang="en">\n<button title="a>b" aria-hidden="true">x</button>\n</html>\n'
    fixed, _ = _fix(tmp_path, source.encode())
    assert fixed.decode() == source.replace(' aria-hidden="true"', "")


# ── The drafter ─────────────────────────────────────────────────────────────


@pytest.fixture
def drafted(monkeypatch, tmp_path: Path) -> list[str]:
    """Stub the model; the alt names the file it was asked about."""
    asked: list[str] = []

    def describe(src: str, **_: object) -> str:
        asked.append(Path(src).name)
        return f"draft-{Path(src).stem}é"

    monkeypatch.setitem(sys.modules, "alt_from_ollama", _Engine(describe))
    for name in ("a.png", "b.png"):
        (tmp_path / name).write_bytes(b"x")
    return asked


class _Engine:
    """The two names ``fill_alt`` imports from the drafting engine."""

    def __init__(self, describe):
        self.describe = describe

    @staticmethod
    def detect_lang() -> str:
        return "en"


def _fill(tmp_path: Path, body: str, encoding: str = "utf-8"):
    page = tmp_path / "page.html"
    page.write_bytes(f'<html lang="fr">\n{body}\n</html>\n'.encode(encoding))
    drafts, left = fill_alt.fill_missing_alt(page)
    return page.read_bytes().decode(encoding).split("\n")[1], drafts, left


def test_two_images_on_a_line_each_get_their_own_alt(tmp_path, drafted) -> None:
    line, drafts, left = _fill(tmp_path, '<img src="a.png"><img src="b.png">')
    assert drafted == ["a.png", "b.png"]
    assert line == '<img alt="draft-aé" src="a.png"><img alt="draft-bé" src="b.png">'
    assert len(drafts) == 2 and not left


def test_an_image_that_has_an_alt_is_passed_over(tmp_path, drafted) -> None:
    line, _, _ = _fill(tmp_path, '<img src="a.png" alt="ok"><img src="b.png">')
    assert drafted == ["b.png"]
    assert line == '<img src="a.png" alt="ok"><img alt="draft-bé" src="b.png">'


def test_an_image_left_alone_does_not_block_its_neighbour(tmp_path, drafted) -> None:
    line, drafts, left = _fill(tmp_path, '<img src="https://x/r.png"><img src="b.png">')
    assert drafted == ["b.png"]
    assert line == '<img src="https://x/r.png"><img alt="draft-bé" src="b.png">'
    assert len(drafts) == 1 and len(left) == 1


def test_data_src_is_not_the_source(tmp_path, drafted) -> None:
    _fill(tmp_path, '<img data-src="a.png" src="b.png">')
    assert drafted == ["b.png"]


def test_a_page_that_is_not_utf8_stays_readable(tmp_path, drafted) -> None:
    line, _, _ = _fill(tmp_path, 'caf\xe9 <img src="a.png">', encoding="latin-1")
    assert line == 'caf\xe9 <img alt="draft-a&#233;" src="a.png">'


# ── An image that cannot be read is said to be so ───────────────────────────


def test_the_command_line_says_the_image_is_missing(tmp_path: Path, capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        alt_main([str(tmp_path / "missing.png")])
    assert stopped.value.code == 2
    captured = capsys.readouterr()
    assert "missing.png" in captured.err
    assert "Traceback" not in captured.err


def test_the_api_answers_404_for_a_url_that_does_not_answer() -> None:
    # Port 1 on the loopback refuses at once: no network, no model.
    response = TestClient(api.app).post(
        "/v1/alt", json={"src": "http://127.0.0.1:1/a.png", "lang": "en"}
    )
    assert response.status_code == 404


# ── What the MCP server says about itself ───────────────────────────────────


def test_the_mcp_server_announces_its_version_as_a_version() -> None:
    """fastapi-mcp 0.4 passes the description into the version slot."""
    from sprezzature_accessibility import __version__
    from sprezzature_accessibility.mcp import mcp

    options = mcp.server.create_initialization_options()
    assert options.server_version == __version__
    assert options.instructions == mcp.description

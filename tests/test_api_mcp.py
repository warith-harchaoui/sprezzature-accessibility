"""
Tests for the HTTP and MCP surfaces.

The rules themselves are covered by ``test_accessibility.py``; what these
guard is the wiring — a route that stops matching its model, an
``operation_id`` renamed so an agent's tool vanishes, or a fastapi-mcp
upgrade that moves ``mount()``. Each of those fails quietly rather than
loudly, which is why they get a test.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from sprezzature_accessibility.api import app  # noqa: E402

client = TestClient(app)


def test_health() -> None:
    """The liveness probe answers."""
    assert client.get("/health").json() == {"status": "ok"}


def test_rules_are_listed_with_severities() -> None:
    """Every rule is advertised, so a caller can choose what to ignore."""
    rules = client.get("/v1/rules").json()["rules"]
    assert len(rules) >= 20
    ids = {r["id"] for r in rules}
    assert "img-missing-alt" in ids
    assert "video-missing-captions" in ids
    assert all(r["severity"] in ("error", "warning") for r in rules)


def test_lint_finds_a_missing_alt() -> None:
    """The canonical violation is reported, with its line."""
    result = client.post("/v1/lint", json={"html": '<img src="a.png">'}).json()
    assert any(f["rule"] == "img-missing-alt" for f in result["findings"])
    assert result["errors"] >= 1


def test_clean_markup_reports_nothing() -> None:
    """A test that only ever finds faults would pass on a broken linter."""
    html = '<html lang="en"><body><img src="a.png" alt="A cat"></body></html>'
    result = client.post("/v1/lint", json={"html": html}).json()
    assert result["findings"] == [], result["findings"]


def test_ignore_suppresses_a_rule() -> None:
    """Suppression is honoured, and only for the named rule."""
    html = '<img src="a.png">'
    before = client.post("/v1/lint", json={"html": html}).json()
    after = client.post(
        "/v1/lint", json={"html": html, "ignore": ["img-missing-alt"]}
    ).json()
    assert before["errors"] > after["errors"]


def test_fragment_needs_no_document_wrapper() -> None:
    """Callers lint template fragments; requiring <html> would be useless."""
    result = client.post("/v1/lint", json={"html": '<button></button>'}).json()
    assert any(f["rule"] == "button-empty" for f in result["findings"])


def test_openapi_names_every_tool() -> None:
    """Each route carries an operation_id: that *is* the MCP tool name."""
    paths = client.get("/openapi.json").json()["paths"]
    for path, methods in paths.items():
        for verb, spec in methods.items():
            assert "operationId" in spec, f"{verb.upper()} {path} has no operation_id"


def test_mcp_mounts_and_publishes_the_tools() -> None:
    """The MCP endpoint exists and carries the expected tool names."""
    pytest.importorskip("fastapi_mcp")
    from sprezzature_accessibility.mcp import mcp

    assert mcp is not None
    mounted = {getattr(r, "path", "") for r in app.routes}
    assert any(p.startswith("/mcp") for p in mounted), sorted(mounted)
    assert "lint_html" in {t.name for t in mcp.tools}


def _documented_routes(app):
    """This package's own tools -- fastapi-mcp mounts its transport route on
    the same app, and that one is not ours to document."""
    return [
        route
        for route in app.routes
        if getattr(route, "operation_id", None)
        and not getattr(route, "path", "").startswith("/mcp")
    ]


def test_every_tool_has_a_written_summary() -> None:
    """The first line an MCP host shows is FastAPI's `summary`, and its
    default is the function name title-cased: `cvd` became "Cvd", `wer`
    became "Wer". An agent choosing between tools from several servers reads
    those headlines and little else, so each has to be a written phrase
    saying what the tool does -- not a restatement of the Python identifier.
    """
    from sprezzature_accessibility.api import app

    for route in _documented_routes(app):
        summary = (getattr(route, "summary", "") or "").strip()
        assert summary, f"{route.operation_id}: no summary, so the headline is a function name"
        derived = getattr(route, "name", "").replace("_", " ").title()
        assert summary != derived, (
            f"{route.operation_id}: summary {summary!r} is FastAPI's default (the "
            f"function name title-cased). Write one that says what the tool does."
        )
        assert " " in summary and len(summary) > 15, (
            f"{route.operation_id}: summary {summary!r} is too terse to route on."
        )


def test_every_tool_says_when_to_call_it() -> None:
    """A description that only restates the summary does not help an agent
    choose. Each route's docstring carries the deciding context: when to
    reach for it, what it needs first, or what it must not be used for.
    """
    from sprezzature_accessibility.api import app

    for route in _documented_routes(app):
        description = (getattr(route, "description", "") or "").strip()
        assert len(description) > 120, (
            f"{route.operation_id}: description is {len(description)} chars. Say when "
            f"to call it, not just what it is."
        )

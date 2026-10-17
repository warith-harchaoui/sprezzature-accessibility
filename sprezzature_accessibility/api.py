"""
sprezzature-accessibility: the FastAPI HTTP surface.

Module summary
--------------
Exposes the accessibility linter over HTTP, so a CI job in any language, a
CMS preview, or an editor plugin can check markup without shelling out to
Python. Every route calls :func:`lint_a11y.lint_html` — the same function
the command line calls — so the HTTP answer and the terminal answer cannot
disagree.

What ships here
---------------
- ``GET  /health``: a liveness probe.
- ``GET  /v1/rules``: every rule this build knows, with its severity.
- ``POST /v1/lint``: lint a string of HTML and return the findings.

Why lint a string rather than a URL
------------------------------------
Fetching a URL on a caller's behalf turns this service into an open proxy:
anything that can reach the API can then reach whatever the API can reach,
including a cloud metadata endpoint or an internal host. The caller fetches
its own markup and posts it; the linter stays a pure function of its input.

Install the extra to get the runtime dependencies::

    pip install 'sprezzature-accessibility[api]'

Then run the app with any ASGI server::

    uvicorn sprezzature_accessibility.api:app --host 0.0.0.0 --port 8000

Usage example
-------------
>>> # curl -X POST localhost:8000/v1/lint \\
>>> #      -H 'content-type: application/json' \\
>>> #      -d '{"html": "<img src=\\"a.png\\">"}'
>>> # Full OpenAPI docs at http://localhost:8000/docs

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import RedirectResponse
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError(
        "The FastAPI HTTP surface requires the [api] extra. "
        "Install with: pip install 'sprezzature-accessibility[api]'"
    ) from exc

from pydantic import BaseModel, Field

# The rules live in the scripts package, which is where the command line
# reaches them too; importing rather than re-implementing is the whole point.
# Two layouts, one import. In this checkout the modules sit in scripts/;
# installed from a wheel they ship as the sprezzature_accessibility_scripts package.
# Either way what goes on the path is the directory holding them, because
# they import each other by bare name — that is the same property that lets
# each one run on its own out of a downloaded zip.
_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if not _SCRIPTS.is_dir():  # pragma: no cover - installed layout
    import sprezzature_accessibility_scripts

    _SCRIPTS = Path(sprezzature_accessibility_scripts.__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS))
from lint_a11y import ALL_RULES, lint_html  # noqa: E402

from . import __version__ as _VERSION  # noqa: E402

#: Severity per rule. Errors lock a visitor out; warnings make the page
#: harder to use. The split is the linter's own, surfaced here so a caller
#: can fail a build on errors alone.
_SEVERITY: dict[str, str] = {
    "img-redundant-aria": "warning",
    "color-only-state": "warning",
    "motion-no-reduce-guard": "warning",
    "body-text-tracking-tight": "warning",
    "track-missing-srclang": "warning",
}

app = FastAPI(
    title="Sprezzature Accessibility API",
    description=(
        "HTTP surface for sprezzature-accessibility: a WCAG-oriented HTML "
        "linter covering images, controls, headings, motion and time-based media."
    ),
    version=_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)


class LintRequest(BaseModel):
    """Body for ``POST /v1/lint``."""

    html: str = Field(description="HTML source. A fragment is fine; no document wrapper required.")
    ignore: list[str] = Field(
        default_factory=list,
        description="Rule identifiers to suppress, e.g. [\"color-only-state\"].",
    )


@app.get(
    "/health",
    tags=["meta"],
    operation_id="health",
    summary="Check that this accessibility server is up",
)
def health() -> dict:
    """
    Liveness probe — no dependency check, just proves the app is up.

    Call this only to diagnose a connection problem.

    Returns
    -------
    dict
        ``{"status": "ok"}``.
    """
    return {"status": "ok"}


@app.get(
    "/v1/rules",
    tags=["meta"],
    operation_id="list_rules",
    summary="List the accessibility rules this linter checks",
)
def rules() -> dict:
    """
    Every rule this build knows, with its severity.

    Call this to answer "what do you actually check", and before using
    `lint_html`'s `ignore` list -- a rule id that does not exist is silently
    ignored, so suppressing a finding by a guessed name suppresses nothing.
    It also draws the boundary honestly: what is not in this list is not
    checked, and a clean lint is not a claim of WCAG conformance.

    Returns
    -------
    dict
        ``{"rules": [{"id": ..., "severity": "error" | "warning"}, ...]}``.
    """
    return {
        "rules": [
            {"id": name, "severity": _SEVERITY.get(name, "error")}
            for name in sorted(ALL_RULES)
        ]
    }


@app.post(
    "/v1/lint",
    tags=["actions"],
    operation_id="lint_html",
    summary="Find accessibility faults in a page's HTML",
)
def lint(request: LintRequest) -> dict:
    """
    Lint a string of HTML and report every violation found.

    This is the tool for "check this for accessibility", "a11y lint", "is
    this WCAG-friendly", "missing alt", "unlabelled input", "vérifie
    l'accessibilité" -- and the one to run over any markup you just wrote,
    before showing it to anyone.

    It reads the source only: no browser, no runtime DOM, so it is fast and
    deterministic, and it cannot see what JavaScript builds, what focus does,
    or what colour contrast computes to. A clean result means "none of the
    listed rules fired", never "this page is accessible". Say that when you
    report it, and send colour questions to sprezzature-colors.

    Parameters
    ----------
    request : LintRequest
        The markup and any rules to suppress.

    Returns
    -------
    dict
        ``findings`` (line, rule, severity, message), plus counts by
        severity so a caller can fail a build on ``errors`` alone.
    """
    findings = lint_html(request.html, set(request.ignore))
    rows = [
        {
            "line": f.line,
            "rule": f.rule,
            "severity": _SEVERITY.get(f.rule, "error"),
            "message": f.message,
        }
        for f in findings
    ]
    return {
        "findings": rows,
        "errors": sum(1 for r in rows if r["severity"] == "error"),
        "warnings": sum(1 for r in rows if r["severity"] == "warning"),
    }


@app.get("/docs-redirect", include_in_schema=False)
def docs_redirect() -> RedirectResponse:
    """Convenience redirect to the interactive API docs."""
    return RedirectResponse(url="/docs")


#: What each purpose is for, in the words the decision tree uses. Served
#: rather than documented only, because a caller choosing a ``kind`` is
#: making the one judgement the model cannot make for them.
KIND_HELP: dict[str, str] = {
    "informative": "Carries meaning the surrounding text does not. Describe it.",
    "decorative": "Adds nothing a reader would miss. Takes alt=\"\" — no words.",
    "functional": "Is a control or a link. Describe the *action*, not the picture.",
    "text": "Is words as an image. Transcribe them.",
    "complex": "A chart or diagram. Short alt plus a long description nearby.",
    "group": "One of several images that only make sense together.",
}


# ── The drafting half ────────────────────────────────────────────────────
#
# Served only when the ``[alt]`` extra is installed. The audit routes above
# have no dependencies beyond FastAPI itself; these need a model client, and
# a deployment that only wants the lint should not be forced to carry one.
# A missing extra is reported per-request as a 503 rather than at import, so
# `GET /health` and the lint keep answering.
try:
    from sprezzature_accessibility import (
        DEFAULT_BASE,
        KINDS,
        MAX_CHARS,
        describe,
        describe_long,
        detect_lang,
    )
    _ALT_READY = True
except ImportError:  # pragma: no cover - dependency guard
    _ALT_READY = False
    DEFAULT_BASE, MAX_CHARS = "qwen3-vl:8b", 125
    from sprezzature_accessibility import KINDS


class AltRequest(BaseModel):
    """One image, and the single judgement the model cannot make for you."""

    src: str = Field(
        description="Path or URL to the image. Ignored when kind is 'decorative'.",
        examples=["hero.jpg"],
    )
    kind: Literal[
        "informative", "decorative", "functional", "text", "complex", "group"
    ] = Field(
        default="informative",
        description="Image purpose, per the W3C alt decision tree.",
    )
    lang: str | None = Field(
        default=None,
        description="BCP-47 base tag. Omit to detect from the environment.",
        examples=["fr"],
    )
    context: str = Field(
        default="",
        description=(
            "Surrounding-text hint. For kind='functional' this is where you "
            "name the action or destination."
        ),
    )
    resize: int = Field(
        default=1024, ge=0,
        description="Longest edge sent to the model, in pixels. 0 disables resizing.",
    )
    model: str | None = Field(
        default=None,
        description=f"Ollama tag. Omit for the one authorized model ({DEFAULT_BASE}).",
    )
    vocabulary: list[str] | None = Field(
        default=None,
        description="Project spellings to bias toward instead of a near-miss.",
    )
    long: bool = Field(
        default=False,
        description=(
            "Return a long description as well — what a 'complex' image needs "
            "beside its short alt."
        ),
    )


class AltResponse(BaseModel):
    """The draft, and enough context to judge it."""

    alt: str = Field(description=f"Alt text, at most {MAX_CHARS} characters.")
    long: str | None = Field(
        default=None, description="Long description, when it was asked for."
    )
    lang: str = Field(description="Language the text was written in.")
    kind: str = Field(description="Purpose the caller declared.")
    draft: bool = Field(
        default=True,
        description=(
            "Always true. A model cannot know what an image is for on your "
            "page; verify before committing."
        ),
    )


@app.get(
    "/v1/kinds",
    tags=["meta"],
    operation_id="list_kinds",
    summary="List the six image purposes alt text is written against",
)
def list_kinds() -> dict[str, str]:
    """The six image purposes, each with what it is for.

    Published because choosing between them is the caller's decision and the
    whole quality of the result rests on it.
    """
    return {kind: KIND_HELP[kind] for kind in KINDS}


@app.post(
    "/v1/alt",
    tags=["actions"],
    operation_id="draft_alt_text",
    summary="Draft alt text for one image with a local vision model",
)
def draft_alt_text(request: AltRequest) -> AltResponse:
    """Draft alt text for one image.

    Raises
    ------
    HTTPException
        ``502`` when the local model cannot be reached or refuses the
        request. Reported as a gateway error rather than a server error
        because the failure is upstream of this process, and the fix is to
        start Ollama rather than to retry here.
    """
    if not _ALT_READY:
        raise HTTPException(
            status_code=503,
            detail=(
                "the drafting half is not installed. "
                "pip install 'sprezzature-accessibility[alt]'"
            ),
        )
    language = request.lang or detect_lang()
    try:
        alt = describe(
            request.src,
            kind=request.kind,
            lang=language,
            context=request.context,
            resize=request.resize,
            model=request.model,
            vocabulary=request.vocabulary,
        )
        # No `vocabulary` here: `describe_long` does not take one. The long
        # description is prose a reader will read in full, where a near-miss
        # spelling is visible and correctable; the short alt is a single
        # attribute nobody re-reads, which is where the bias earns its place.
        long_text = (
            describe_long(
                request.src,
                kind=request.kind,
                lang=language,
                context=request.context,
                resize=request.resize,
                model=request.model,
            )
            if request.long
            else None
        )
    except SystemExit as exc:
        # The script layer exits on an unreachable model; over HTTP that has
        # to become a status code, not a dead worker.
        raise HTTPException(
            status_code=502,
            detail=(
                f"the local vision model could not be reached "
                f"(exit {exc.code}). Is Ollama running, and is "
                f"{DEFAULT_BASE} pulled?"
            ),
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return AltResponse(alt=alt, long=long_text, lang=language, kind=request.kind)

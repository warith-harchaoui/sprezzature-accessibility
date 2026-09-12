"""
sprezzature-accessibility — Model Context Protocol (MCP) surface.

Adapter that republishes the FastAPI app in :mod:`sprezzature_accessibility.api`
as MCP tools, so any MCP-aware host — an agent runtime, an IDE integration,
a custom shell — can call ``check_contrast`` / ``simulate_color_blindness``
/ ``get_palette`` as first-class tools instead of guessing at a shell
command. Uses :mod:`fastapi_mcp` (https://github.com/tadata-org/fastapi_mcp):
one wrapper over the whole existing HTTP surface, so the routes serve both
plain HTTP callers and MCP hosts without being written twice.

Why a wrapper rather than a hand-written server
-----------------------------------------------
A hand-written MCP server would be a second description of the same
surface, free to drift from the routes it claims to mirror — a tool whose
argument names quietly disagree with the API is worse than no tool, because
the disagreement only shows up at call time. Deriving the tools from the
FastAPI signatures means the two cannot disagree: the ``operation_id`` on
each route *is* the tool name, and the Pydantic model *is* the schema.

Why colour checks are worth giving an agent
--------------------------------------------
These are questions with defensible answers rather than opinions. A contrast
ratio is defined by WCAG; a colour-vision simulation is a published matrix.
An assistant asked "is this palette accessible?" can now answer with a
number it computed instead of an impression it formed — and be wrong in a
way that is checkable.

Install the extra to pull in ``fastapi-mcp``::

    pip install 'sprezzature-accessibility[api,mcp]'

Then run the MCP server::

    sprezzature-accessibility-mcp          # entry point (see pyproject)
    # or, equivalently:
    python -m sprezzature_accessibility.mcp

Usage Example
-------------
>>> # Register the MCP endpoint in your client. It publishes:
>>> #   health / list_rules / lint_html
>>> # ...with the same argument names as the FastAPI routes.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

try:
    from fastapi_mcp import FastApiMCP
except ImportError as exc:  # pragma: no cover - dependency guard
    raise ImportError(
        "The MCP surface requires the [mcp] extra. "
        "Install with: pip install 'sprezzature-accessibility[api,mcp]'"
    ) from exc

# Reuse the exact same FastAPI app -- MCP is a thin wrapper on top.
from sprezzature_accessibility.api import app

# FastApiMCP mounts an MCP endpoint on the existing FastAPI app; the wrapped
# instance is kept at module scope so downstream code (tests, ASGI runners)
# can reach both the FastAPI app and the MCP handler.
mcp = FastApiMCP(
    app,
    name="sprezzature-accessibility",
    description=(
        "Sprezzature Accessibility MCP tools: lint HTML against a WCAG-oriented "
        "rule set covering images, controls, headings, motion and captions."
    ),
    include_tags=["meta", "actions"],
)
# Newer fastapi-mcp releases split mount() into transport-specific
# mount_http() (recommended) and mount_sse(); fall back to the legacy
# mount() on older versions so a range of fastapi-mcp versions still work.
if hasattr(mcp, "mount_http"):
    mcp.mount_http()
else:  # pragma: no cover - legacy fastapi-mcp
    mcp.mount()


def main() -> None:
    """
    Entry point for the ``sprezzature-accessibility-mcp`` console script.

    Boots the FastAPI app — which now serves both the HTTP routes and the
    MCP endpoint — with ``uvicorn``. Meant for local or container usage;
    behind a real load balancer, run ``uvicorn``/``gunicorn`` directly.
    """
    import os

    import uvicorn

    host = os.environ.get("SPREZZATURE_COLORS_HOST", "0.0.0.0")
    port = int(os.environ.get("SPREZZATURE_COLORS_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, workers=1)


if __name__ == "__main__":  # pragma: no cover
    main()

"""
The container answers ``/mcp`` as well as ``/v1/...``.

The Dockerfile ran ``uvicorn sprezzature_accessibility.api:app``. That app
gets its MCP endpoint only when ``sprezzature_accessibility.mcp`` is imported,
and uvicorn on ``api:app`` never imports it, so the image served the HTTP
routes and no ``/mcp``, and the README said so as if it were a design.

``test_api_mcp.py`` already proves the MCP module mounts the endpoint; this
file proves the image and the compose service start that module, on all
interfaces.

Author
------
Warith HARCHAOUI <warithmetics@deraison.ai>
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER = "sprezzature-accessibility-mcp"


def test_the_dockerfile_cmd_is_the_mcp_server() -> None:
    text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")
    cmds = re.findall(r"^CMD\s+(.+)$", text, re.MULTILINE)
    assert cmds, "the Dockerfile has no CMD"
    last = cmds[-1]
    assert SERVER in last and "0.0.0.0" in last, (
        f"the image's CMD is {last}; it has to run {SERVER} on 0.0.0.0 so one "
        f"port serves the HTTP routes and /mcp."
    )


def test_the_compose_service_runs_the_mcp_server() -> None:
    text = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    commands = re.findall(r"^\s+command:\s*(.+)$", text, re.MULTILINE)
    assert any(SERVER in c and "0.0.0.0" in c for c in commands), (
        f"docker-compose.yml does not run {SERVER} on 0.0.0.0: {commands}"
    )

"""
test_the_front_door_passes_help_on — `sprezzature-accessibility TOOL --help` is the tool's help.

The front door registers each tool as a sub-command that forwards its
arguments. With a help option of its own, that stub answered `--help` with
one line and a REST argument, and only `TOOL -- --help` reached the flags
anybody was asking about.

Author
------
`Warith HARCHAOUI, Ph.D. <https://www.linkedin.com/in/warith-harchaoui/>`_
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from sprezzature_accessibility._tools import TOOLS
from sprezzature_accessibility.cli import main


@pytest.mark.parametrize("tool", sorted(TOOLS))
def test_tool_help_is_the_tools_own(tool: str) -> None:
    result = CliRunner().invoke(main, [tool, "--help"])
    assert result.exit_code == 0, result.output
    assert "[REST]" not in result.output, result.output
    assert "Options:" in result.output

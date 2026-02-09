"""Public API for ticktick-cli."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from ticktick_cli.app import cli_main, main
from ticktick_cli.commands import (
    ALL_TOOLS,
    TOOL_MODULES,
    _run_projects_command,
    _run_tasks_command,
    resolve_enabled_tools,
    run_auth,
    run_data_cli,
    run_server,
)
from ticktick_cli.common import get_version, load_dotenv_if_available
from ticktick_cli.parser import create_parser

try:
    __version__ = version("ticktick-cli")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = [
    "ALL_TOOLS",
    "TOOL_MODULES",
    "__version__",
    "_run_projects_command",
    "_run_tasks_command",
    "cli_main",
    "create_parser",
    "get_version",
    "load_dotenv_if_available",
    "main",
    "resolve_enabled_tools",
    "run_auth",
    "run_data_cli",
    "run_server",
]

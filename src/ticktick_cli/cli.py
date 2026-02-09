#!/usr/bin/env python3
"""Compatibility wrapper for the ticktick-cli package."""

from __future__ import annotations

from ticktick_cli import (
    ALL_TOOLS,
    TOOL_MODULES,
    _run_projects_command,
    _run_tasks_command,
    cli_main,
    create_parser,
    get_version,
    load_dotenv_if_available,
    main,
    resolve_enabled_tools,
    run_auth,
    run_data_cli,
    run_server,
)

__all__ = [
    "ALL_TOOLS",
    "TOOL_MODULES",
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


if __name__ == "__main__":
    cli_main()

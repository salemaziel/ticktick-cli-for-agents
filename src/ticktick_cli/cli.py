#!/usr/bin/env python3
"""Compatibility wrapper for the ticktick-cli package."""

from __future__ import annotations

from ticktick_cli import (
    _run_projects_command,
    _run_tasks_command,
    cli_main,
    create_parser,
    get_version,
    load_dotenv_if_available,
    main,
    run_auth,
    run_data_cli,
)

__all__ = [
    "_run_projects_command",
    "_run_tasks_command",
    "cli_main",
    "create_parser",
    "get_version",
    "load_dotenv_if_available",
    "main",
    "run_auth",
    "run_data_cli",
]


if __name__ == "__main__":
    cli_main()

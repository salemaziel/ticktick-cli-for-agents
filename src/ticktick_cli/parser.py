"""Argument parser construction for ticktick-cli."""

from __future__ import annotations

import argparse

from ticktick_cli.common import get_version


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="ticktick",
        description="TickTick CLI - command-line interface for ticktick-sdk",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  %(prog)s                  Start the MCP server (default)
  %(prog)s server           Start the MCP server (explicit)
  %(prog)s auth             Get OAuth2 token (opens browser)
  %(prog)s auth --manual    Get OAuth2 token (SSH-friendly)
  %(prog)s tasks list       List tasks in current project
  %(prog)s projects list    List projects
""",
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {get_version()}",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON when supported by the command.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        title="commands",
        description="Available commands (default: server)",
        metavar="<command>",
    )

    server_parser = subparsers.add_parser(
        "server",
        help="Run the MCP server for AI assistant integration",
        description="""\
Run the TickTick MCP server.

This starts the FastMCP server that exposes TickTick functionality
as tools for AI assistants. The server communicates via stdio and
implements the Model Context Protocol.

Before running the server, ensure your environment variables are set:
  - TICKTICK_CLIENT_ID
  - TICKTICK_CLIENT_SECRET
  - TICKTICK_ACCESS_TOKEN
  - TICKTICK_USERNAME
  - TICKTICK_PASSWORD

Tool Filtering:
  Use --enabledTools or --enabledModules to load only the tools you need.

Available modules: tasks, projects, folders, columns, tags, habits, user, focus
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    server_parser.add_argument(
        "--enabledTools",
        type=str,
        default=None,
        metavar="TOOLS",
        help=(
            "Comma-separated list of specific tools to enable. "
            "Example: --enabledTools ticktick_create_tasks,ticktick_list_tasks"
        ),
    )

    server_parser.add_argument(
        "--enabledModules",
        type=str,
        default=None,
        metavar="MODULES",
        help=(
            "Comma-separated list of tool modules to enable. "
            "Available: tasks, projects, folders, columns, tags, habits, user, focus. "
            "Example: --enabledModules tasks,projects"
        ),
    )

    server_parser.add_argument(
        "--host",
        type=str,
        default=None,
        metavar="HOST",
        help=(
            "API host to use. Options: ticktick.com (international, default), "
            "dida365.com (Chinese version). "
            "Can also be set via TICKTICK_HOST environment variable."
        ),
    )

    server_parser.add_argument(
        "--json",
        action="store_true",
        help="Accepted for consistency; server output remains stdio/MCP.",
    )

    auth_parser = subparsers.add_parser(
        "auth",
        help="Get OAuth2 access token for TickTick API",
        description="""\
Get an OAuth2 access token for the TickTick V1 API.

This command guides you through the OAuth2 authorization flow:
1. Opens your browser to TickTick's authorization page
2. Waits for you to authorize the application
3. Exchanges the authorization code for an access token
4. Displays the token for you to copy to your .env file

Before running this command, ensure these environment variables are set:
  - TICKTICK_CLIENT_ID
  - TICKTICK_CLIENT_SECRET

The redirect URI defaults to http://127.0.0.1:8080/callback
but can be customized with TICKTICK_REDIRECT_URI.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  ticktick auth             Opens browser for authorization
  ticktick auth --manual    Prints URL for manual authorization (SSH-friendly)
""",
    )

    auth_parser.add_argument(
        "--manual",
        "-m",
        action="store_true",
        help="Manual mode: prints URL for you to visit (SSH-friendly)",
    )

    auth_parser.add_argument(
        "--json",
        action="store_true",
        help="Accepted for consistency; auth output remains interactive text.",
    )

    tasks_parser = subparsers.add_parser(
        "tasks",
        help="Manage tasks from the command line",
    )
    tasks_subparsers = tasks_parser.add_subparsers(
        dest="tasks_command",
        metavar="<action>",
        required=True,
    )

    tasks_list_parser = tasks_subparsers.add_parser(
        "list",
        help="List active tasks for the current project",
    )
    tasks_list_parser.add_argument(
        "--project",
        dest="project_id",
        default=None,
        help="Project ID. Defaults to current project (or inbox).",
    )
    tasks_list_parser.add_argument(
        "--due",
        type=str,
        default=None,
        help="Filter by local due date (YYYY-MM-DD).",
    )
    tasks_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output tasks as JSON.",
    )

    tasks_add_parser = tasks_subparsers.add_parser(
        "add",
        help="Create a task in the current project",
    )
    tasks_add_parser.add_argument(
        "title",
        type=str,
        help="Task title",
    )
    tasks_add_parser.add_argument(
        "--project",
        dest="project_id",
        default=None,
        help="Project ID. Defaults to current project (or inbox).",
    )
    tasks_add_parser.add_argument(
        "--due",
        type=str,
        default=None,
        help="Due value: YYYY-MM-DD or ISO datetime.",
    )
    tasks_add_parser.add_argument(
        "--content",
        type=str,
        default=None,
        help="Task notes/content.",
    )
    tasks_add_parser.add_argument(
        "--priority",
        choices=["none", "low", "medium", "high"],
        default=None,
        help="Task priority.",
    )
    tasks_add_parser.add_argument(
        "--json",
        action="store_true",
        help="Output created task as JSON.",
    )

    tasks_done_parser = tasks_subparsers.add_parser(
        "done",
        help="Mark a task as completed",
    )
    tasks_done_parser.add_argument("task_id", type=str, help="Task ID")
    tasks_done_parser.add_argument(
        "--project",
        dest="project_id",
        default=None,
        help="Project ID (optional; auto-resolved when omitted).",
    )
    tasks_done_parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON.",
    )

    tasks_abandon_parser = tasks_subparsers.add_parser(
        "abandon",
        help="Mark a task as abandoned (won't do)",
    )
    tasks_abandon_parser.add_argument("task_id", type=str, help="Task ID")
    tasks_abandon_parser.add_argument(
        "--project",
        dest="project_id",
        default=None,
        help="Project ID (optional; auto-resolved when omitted).",
    )
    tasks_abandon_parser.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON.",
    )

    projects_parser = subparsers.add_parser(
        "projects",
        help="Manage projects from the command line",
    )
    projects_subparsers = projects_parser.add_subparsers(
        dest="projects_command",
        metavar="<action>",
        required=True,
    )

    projects_list_parser = projects_subparsers.add_parser(
        "list",
        help="List projects",
    )
    projects_list_parser.add_argument(
        "--json",
        action="store_true",
        help="Output projects as JSON.",
    )

    return parser

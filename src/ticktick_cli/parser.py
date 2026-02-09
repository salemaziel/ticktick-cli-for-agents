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

    def _add_project_argument(command_parser: argparse.ArgumentParser, *, required: bool = False) -> None:
        command_parser.add_argument(
            "--project",
            dest="project_id",
            default=None,
            required=required,
            help="Project ID.",
        )

    def _add_json_argument(command_parser: argparse.ArgumentParser, *, help_text: str) -> None:
        command_parser.add_argument(
            "--json",
            action="store_true",
            help=help_text,
        )

    tasks_parser = subparsers.add_parser(
        "tasks",
        help="Manage tasks from the command line",
        description="Task management commands covering single and batch operations.",
    )
    tasks_subparsers = tasks_parser.add_subparsers(
        dest="tasks_command",
        metavar="<action>",
        required=True,
    )

    tasks_list_parser = tasks_subparsers.add_parser(
        "list",
        help="List active tasks (defaults to current project/inbox)",
    )
    _add_project_argument(tasks_list_parser)
    tasks_list_parser.add_argument(
        "--due",
        type=str,
        default=None,
        help="Filter by local due date (YYYY-MM-DD).",
    )
    _add_json_argument(tasks_list_parser, help_text="Output tasks as JSON.")

    tasks_get_parser = tasks_subparsers.add_parser(
        "get",
        help="Get a task by ID",
    )
    tasks_get_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_get_parser)
    _add_json_argument(tasks_get_parser, help_text="Output task as JSON.")

    tasks_add_parser = tasks_subparsers.add_parser(
        "add",
        help="Create a task",
    )
    tasks_add_parser.add_argument("title", type=str, help="Task title")
    _add_project_argument(tasks_add_parser)
    tasks_add_parser.add_argument(
        "--content",
        type=str,
        default=None,
        help="Task notes/content.",
    )
    tasks_add_parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="Checklist description (desc field).",
    )
    tasks_add_parser.add_argument(
        "--kind",
        choices=["TEXT", "NOTE", "CHECKLIST", "text", "note", "checklist"],
        default=None,
        help="Task kind/type.",
    )
    tasks_add_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start value: YYYY-MM-DD or ISO datetime.",
    )
    tasks_add_parser.add_argument(
        "--due",
        type=str,
        default=None,
        help="Due value: YYYY-MM-DD or ISO datetime.",
    )
    tasks_add_parser.add_argument(
        "--priority",
        choices=["none", "low", "medium", "high"],
        default=None,
        help="Task priority.",
    )
    tasks_add_parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated tags.",
    )
    tasks_add_parser.add_argument(
        "--recurrence",
        type=str,
        default=None,
        help="RRULE recurrence value (requires --start).",
    )
    tasks_add_parser.add_argument(
        "--time-zone",
        dest="time_zone",
        type=str,
        default=None,
        help="IANA timezone to store on task (default: TZ/local).",
    )
    add_all_day_group = tasks_add_parser.add_mutually_exclusive_group()
    add_all_day_group.add_argument(
        "--all-day",
        action="store_true",
        help="Mark task as all-day.",
    )
    add_all_day_group.add_argument(
        "--timed",
        action="store_true",
        help="Mark task as timed (not all-day).",
    )
    tasks_add_parser.add_argument(
        "--parent",
        dest="parent_id",
        type=str,
        default=None,
        help="Parent task ID (create as subtask).",
    )
    tasks_add_parser.add_argument(
        "--reminders",
        type=str,
        default=None,
        help="Comma-separated reminder triggers (e.g. TRIGGER:-PT30M).",
    )
    _add_json_argument(tasks_add_parser, help_text="Output created task as JSON.")

    tasks_quick_add_parser = tasks_subparsers.add_parser(
        "quick-add",
        help="Quick add a task with just text/title",
    )
    tasks_quick_add_parser.add_argument("text", type=str, help="Task text/title")
    _add_project_argument(tasks_quick_add_parser)
    _add_json_argument(tasks_quick_add_parser, help_text="Output created task as JSON.")

    tasks_update_parser = tasks_subparsers.add_parser(
        "update",
        help="Update a task",
    )
    tasks_update_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_update_parser)
    tasks_update_parser.add_argument("--title", type=str, default=None, help="New title.")
    tasks_update_parser.add_argument("--content", type=str, default=None, help="New content.")
    tasks_update_parser.add_argument(
        "--description",
        type=str,
        default=None,
        help="New checklist description.",
    )
    tasks_update_parser.add_argument(
        "--kind",
        choices=["TEXT", "NOTE", "CHECKLIST", "text", "note", "checklist"],
        default=None,
        help="New task kind/type.",
    )
    tasks_update_parser.add_argument(
        "--priority",
        choices=["none", "low", "medium", "high"],
        default=None,
        help="New priority.",
    )
    tasks_update_parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Set start value (YYYY-MM-DD or ISO datetime).",
    )
    tasks_update_parser.add_argument(
        "--clear-start",
        action="store_true",
        help="Clear task start date.",
    )
    tasks_update_parser.add_argument(
        "--due",
        type=str,
        default=None,
        help="Set due value (YYYY-MM-DD or ISO datetime).",
    )
    tasks_update_parser.add_argument(
        "--clear-due",
        action="store_true",
        help="Clear task due date.",
    )
    tasks_update_parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Set tags from comma-separated list (replaces existing tags).",
    )
    tasks_update_parser.add_argument(
        "--clear-tags",
        action="store_true",
        help="Clear all tags.",
    )
    tasks_update_parser.add_argument(
        "--recurrence",
        type=str,
        default=None,
        help="Set RRULE recurrence value.",
    )
    tasks_update_parser.add_argument(
        "--clear-recurrence",
        action="store_true",
        help="Clear recurrence rule.",
    )
    tasks_update_parser.add_argument(
        "--time-zone",
        dest="time_zone",
        type=str,
        default=None,
        help="Set explicit timezone on task.",
    )
    update_all_day_group = tasks_update_parser.add_mutually_exclusive_group()
    update_all_day_group.add_argument(
        "--all-day",
        action="store_true",
        help="Mark task as all-day.",
    )
    update_all_day_group.add_argument(
        "--timed",
        action="store_true",
        help="Mark task as timed (not all-day).",
    )
    _add_json_argument(tasks_update_parser, help_text="Output updated task as JSON.")

    tasks_done_parser = tasks_subparsers.add_parser(
        "done",
        help="Mark a task as completed",
    )
    tasks_done_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_done_parser)
    _add_json_argument(tasks_done_parser, help_text="Output result as JSON.")

    tasks_abandon_parser = tasks_subparsers.add_parser(
        "abandon",
        help="Mark a task as abandoned (won't do)",
    )
    tasks_abandon_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_abandon_parser)
    _add_json_argument(tasks_abandon_parser, help_text="Output result as JSON.")

    tasks_delete_parser = tasks_subparsers.add_parser(
        "delete",
        help="Delete a task",
    )
    tasks_delete_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_delete_parser)
    _add_json_argument(tasks_delete_parser, help_text="Output result as JSON.")

    tasks_move_parser = tasks_subparsers.add_parser(
        "move",
        help="Move a task to another project",
    )
    tasks_move_parser.add_argument("task_id", type=str, help="Task ID")
    tasks_move_parser.add_argument(
        "--from-project",
        dest="from_project_id",
        default=None,
        help="Current project ID (auto-resolved when omitted).",
    )
    tasks_move_parser.add_argument(
        "--to-project",
        dest="to_project_id",
        required=True,
        help="Destination project ID.",
    )
    _add_json_argument(tasks_move_parser, help_text="Output result as JSON.")

    tasks_subtask_parser = tasks_subparsers.add_parser(
        "subtask",
        help="Make a task a subtask of another task",
    )
    tasks_subtask_parser.add_argument("task_id", type=str, help="Task ID to make subtask")
    tasks_subtask_parser.add_argument("--parent", dest="parent_id", required=True, help="Parent task ID.")
    _add_project_argument(tasks_subtask_parser)
    _add_json_argument(tasks_subtask_parser, help_text="Output result as JSON.")

    tasks_unparent_parser = tasks_subparsers.add_parser(
        "unparent",
        help="Remove a subtask from its parent",
    )
    tasks_unparent_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_unparent_parser)
    _add_json_argument(tasks_unparent_parser, help_text="Output result as JSON.")

    tasks_pin_parser = tasks_subparsers.add_parser(
        "pin",
        help="Pin a task",
    )
    tasks_pin_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_pin_parser)
    _add_json_argument(tasks_pin_parser, help_text="Output updated task as JSON.")

    tasks_unpin_parser = tasks_subparsers.add_parser(
        "unpin",
        help="Unpin a task",
    )
    tasks_unpin_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_unpin_parser)
    _add_json_argument(tasks_unpin_parser, help_text="Output updated task as JSON.")

    tasks_column_parser = tasks_subparsers.add_parser(
        "column",
        help="Move task to a kanban column",
    )
    tasks_column_parser.add_argument("task_id", type=str, help="Task ID")
    _add_project_argument(tasks_column_parser)
    column_group = tasks_column_parser.add_mutually_exclusive_group(required=True)
    column_group.add_argument("--column", dest="column_id", default=None, help="Target column ID.")
    column_group.add_argument(
        "--clear-column",
        action="store_true",
        help="Remove task from its current column.",
    )
    _add_json_argument(tasks_column_parser, help_text="Output updated task as JSON.")

    tasks_search_parser = tasks_subparsers.add_parser(
        "search",
        help="Search tasks by title/content",
    )
    tasks_search_parser.add_argument("query", type=str, help="Search query")
    _add_project_argument(tasks_search_parser)
    _add_json_argument(tasks_search_parser, help_text="Output matching tasks as JSON.")

    tasks_tag_parser = tasks_subparsers.add_parser(
        "by-tag",
        help="List tasks by tag",
    )
    tasks_tag_parser.add_argument("tag_name", type=str, help="Tag name")
    _add_project_argument(tasks_tag_parser)
    _add_json_argument(tasks_tag_parser, help_text="Output matching tasks as JSON.")

    tasks_priority_parser = tasks_subparsers.add_parser(
        "by-priority",
        help="List tasks by priority",
    )
    tasks_priority_parser.add_argument(
        "priority",
        type=str,
        help="Priority value: none|low|medium|high|0|1|3|5",
    )
    _add_project_argument(tasks_priority_parser)
    _add_json_argument(tasks_priority_parser, help_text="Output matching tasks as JSON.")

    tasks_today_parser = tasks_subparsers.add_parser(
        "today",
        help="List tasks due today",
    )
    _add_project_argument(tasks_today_parser)
    _add_json_argument(tasks_today_parser, help_text="Output tasks as JSON.")

    tasks_overdue_parser = tasks_subparsers.add_parser(
        "overdue",
        help="List overdue tasks",
    )
    _add_project_argument(tasks_overdue_parser)
    _add_json_argument(tasks_overdue_parser, help_text="Output tasks as JSON.")

    tasks_completed_parser = tasks_subparsers.add_parser(
        "completed",
        help="List recently completed tasks",
    )
    tasks_completed_parser.add_argument("--days", type=int, default=7, help="Lookback window in days.")
    tasks_completed_parser.add_argument("--limit", type=int, default=100, help="Maximum tasks to return.")
    _add_project_argument(tasks_completed_parser)
    _add_json_argument(tasks_completed_parser, help_text="Output tasks as JSON.")

    tasks_abandoned_parser = tasks_subparsers.add_parser(
        "abandoned",
        help="List recently abandoned tasks",
    )
    tasks_abandoned_parser.add_argument("--days", type=int, default=7, help="Lookback window in days.")
    tasks_abandoned_parser.add_argument("--limit", type=int, default=100, help="Maximum tasks to return.")
    _add_project_argument(tasks_abandoned_parser)
    _add_json_argument(tasks_abandoned_parser, help_text="Output tasks as JSON.")

    tasks_deleted_parser = tasks_subparsers.add_parser(
        "deleted",
        help="List deleted tasks in trash",
    )
    tasks_deleted_parser.add_argument("--limit", type=int, default=100, help="Maximum tasks to return.")
    _add_project_argument(tasks_deleted_parser)
    _add_json_argument(tasks_deleted_parser, help_text="Output tasks as JSON.")

    tasks_batch_create_parser = tasks_subparsers.add_parser(
        "batch-create",
        help="Create tasks from JSON file",
    )
    tasks_batch_create_parser.add_argument("--file", required=True, help="Path to JSON array of task specs.")
    _add_json_argument(tasks_batch_create_parser, help_text="Output created tasks as JSON.")

    tasks_batch_update_parser = tasks_subparsers.add_parser(
        "batch-update",
        help="Update tasks from JSON file",
    )
    tasks_batch_update_parser.add_argument("--file", required=True, help="Path to JSON array of update specs.")
    _add_json_argument(tasks_batch_update_parser, help_text="Output batch result as JSON.")

    tasks_batch_delete_parser = tasks_subparsers.add_parser(
        "batch-delete",
        help="Delete tasks from JSON file",
    )
    tasks_batch_delete_parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON array of [task_id, project_id] pairs.",
    )
    _add_json_argument(tasks_batch_delete_parser, help_text="Output batch result as JSON.")

    tasks_batch_done_parser = tasks_subparsers.add_parser(
        "batch-done",
        help="Complete tasks from JSON file",
    )
    tasks_batch_done_parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON array of [task_id, project_id] pairs.",
    )
    _add_json_argument(tasks_batch_done_parser, help_text="Output batch result as JSON.")

    tasks_batch_move_parser = tasks_subparsers.add_parser(
        "batch-move",
        help="Move tasks from JSON file",
    )
    tasks_batch_move_parser.add_argument("--file", required=True, help="Path to JSON array of move specs.")
    _add_json_argument(tasks_batch_move_parser, help_text="Output batch result as JSON.")

    tasks_batch_parent_parser = tasks_subparsers.add_parser(
        "batch-parent",
        help="Set parent tasks from JSON file",
    )
    tasks_batch_parent_parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON array of parent assignment specs.",
    )
    _add_json_argument(tasks_batch_parent_parser, help_text="Output batch result as JSON.")

    tasks_batch_unparent_parser = tasks_subparsers.add_parser(
        "batch-unparent",
        help="Remove task parents from JSON file",
    )
    tasks_batch_unparent_parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON array of unparent specs.",
    )
    _add_json_argument(tasks_batch_unparent_parser, help_text="Output batch result as JSON.")

    tasks_batch_pin_parser = tasks_subparsers.add_parser(
        "batch-pin",
        help="Pin/unpin tasks from JSON file",
    )
    tasks_batch_pin_parser.add_argument(
        "--file",
        required=True,
        help="Path to JSON array of pin specs.",
    )
    _add_json_argument(tasks_batch_pin_parser, help_text="Output updated tasks as JSON.")

    projects_parser = subparsers.add_parser(
        "projects",
        help="Manage projects from the command line",
        description="Project management commands.",
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
    _add_json_argument(projects_list_parser, help_text="Output projects as JSON.")

    projects_get_parser = projects_subparsers.add_parser(
        "get",
        help="Get project details by ID",
    )
    projects_get_parser.add_argument("project_id", type=str, help="Project ID")
    _add_json_argument(projects_get_parser, help_text="Output project as JSON.")

    projects_data_parser = projects_subparsers.add_parser(
        "data",
        help="Get project with tasks and columns",
    )
    projects_data_parser.add_argument("project_id", type=str, help="Project ID")
    _add_json_argument(projects_data_parser, help_text="Output project data as JSON.")

    projects_create_parser = projects_subparsers.add_parser(
        "create",
        help="Create a project",
    )
    projects_create_parser.add_argument("name", type=str, help="Project name")
    projects_create_parser.add_argument(
        "--color",
        type=str,
        default=None,
        help="Hex color (e.g. #F18181).",
    )
    projects_create_parser.add_argument(
        "--kind",
        choices=["TASK", "NOTE", "task", "note"],
        default="TASK",
        help="Project kind.",
    )
    projects_create_parser.add_argument(
        "--view",
        dest="view_mode",
        choices=["list", "kanban", "timeline"],
        default="list",
        help="Project view mode.",
    )
    projects_create_parser.add_argument(
        "--folder",
        dest="folder_id",
        default=None,
        help="Folder (project group) ID.",
    )
    _add_json_argument(projects_create_parser, help_text="Output created project as JSON.")

    projects_update_parser = projects_subparsers.add_parser(
        "update",
        help="Update a project",
    )
    projects_update_parser.add_argument("project_id", type=str, help="Project ID")
    projects_update_parser.add_argument("--name", type=str, default=None, help="New name.")
    projects_update_parser.add_argument("--color", type=str, default=None, help="New hex color.")
    projects_update_parser.add_argument(
        "--folder",
        dest="folder_id",
        default=None,
        help="New folder ID.",
    )
    projects_update_parser.add_argument(
        "--remove-folder",
        action="store_true",
        help="Remove project from folder.",
    )
    _add_json_argument(projects_update_parser, help_text="Output updated project as JSON.")

    projects_delete_parser = projects_subparsers.add_parser(
        "delete",
        help="Delete a project",
    )
    projects_delete_parser.add_argument("project_id", type=str, help="Project ID")
    _add_json_argument(projects_delete_parser, help_text="Output result as JSON.")

    folders_parser = subparsers.add_parser(
        "folders",
        help="Manage folders (project groups)",
        description="Folder (project group) management commands.",
    )
    folders_subparsers = folders_parser.add_subparsers(
        dest="folders_command",
        metavar="<action>",
        required=True,
    )

    folders_list_parser = folders_subparsers.add_parser(
        "list",
        help="List folders",
    )
    _add_json_argument(folders_list_parser, help_text="Output folders as JSON.")

    folders_create_parser = folders_subparsers.add_parser(
        "create",
        help="Create a folder",
    )
    folders_create_parser.add_argument("name", type=str, help="Folder name")
    _add_json_argument(folders_create_parser, help_text="Output created folder as JSON.")

    folders_rename_parser = folders_subparsers.add_parser(
        "rename",
        help="Rename a folder",
    )
    folders_rename_parser.add_argument("folder_id", type=str, help="Folder ID")
    folders_rename_parser.add_argument("name", type=str, help="New folder name")
    _add_json_argument(folders_rename_parser, help_text="Output updated folder as JSON.")

    folders_delete_parser = folders_subparsers.add_parser(
        "delete",
        help="Delete a folder",
    )
    folders_delete_parser.add_argument("folder_id", type=str, help="Folder ID")
    _add_json_argument(folders_delete_parser, help_text="Output result as JSON.")

    return parser

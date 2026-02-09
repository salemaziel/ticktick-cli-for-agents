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

    sync_parser = subparsers.add_parser(
        "sync",
        help="Fetch full account sync payload",
    )
    sync_parser.add_argument(
        "--json",
        action="store_true",
        help="Output sync payload as JSON.",
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

    columns_parser = subparsers.add_parser(
        "columns",
        help="Manage kanban columns",
        description="Kanban column management commands.",
    )
    columns_subparsers = columns_parser.add_subparsers(
        dest="columns_command",
        metavar="<action>",
        required=True,
    )

    columns_list_parser = columns_subparsers.add_parser(
        "list",
        help="List columns for a project",
    )
    columns_list_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    _add_json_argument(columns_list_parser, help_text="Output columns as JSON.")

    columns_create_parser = columns_subparsers.add_parser(
        "create",
        help="Create a column",
    )
    columns_create_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    columns_create_parser.add_argument("name", type=str, help="Column name")
    columns_create_parser.add_argument("--sort", dest="sort_order", type=int, default=None, help="Sort order.")
    _add_json_argument(columns_create_parser, help_text="Output created column as JSON.")

    columns_update_parser = columns_subparsers.add_parser(
        "update",
        help="Update a column",
    )
    columns_update_parser.add_argument("column_id", type=str, help="Column ID")
    columns_update_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    columns_update_parser.add_argument("--name", type=str, default=None, help="New column name.")
    columns_update_parser.add_argument("--sort", dest="sort_order", type=int, default=None, help="New sort order.")
    _add_json_argument(columns_update_parser, help_text="Output updated column as JSON.")

    columns_delete_parser = columns_subparsers.add_parser(
        "delete",
        help="Delete a column",
    )
    columns_delete_parser.add_argument("column_id", type=str, help="Column ID")
    columns_delete_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    _add_json_argument(columns_delete_parser, help_text="Output result as JSON.")

    tags_parser = subparsers.add_parser(
        "tags",
        help="Manage tags",
        description="Tag management commands.",
    )
    tags_subparsers = tags_parser.add_subparsers(
        dest="tags_command",
        metavar="<action>",
        required=True,
    )

    tags_list_parser = tags_subparsers.add_parser(
        "list",
        help="List tags",
    )
    _add_json_argument(tags_list_parser, help_text="Output tags as JSON.")

    tags_create_parser = tags_subparsers.add_parser(
        "create",
        help="Create a tag",
    )
    tags_create_parser.add_argument("name", type=str, help="Tag name")
    tags_create_parser.add_argument("--color", type=str, default=None, help="Hex color.")
    tags_create_parser.add_argument("--parent", type=str, default=None, help="Parent tag name.")
    _add_json_argument(tags_create_parser, help_text="Output created tag as JSON.")

    tags_update_parser = tags_subparsers.add_parser(
        "update",
        help="Update a tag",
    )
    tags_update_parser.add_argument("name", type=str, help="Tag name")
    tags_update_parser.add_argument("--color", type=str, default=None, help="New hex color.")
    tags_update_parser.add_argument("--parent", type=str, default=None, help="New parent tag name.")
    tags_update_parser.add_argument(
        "--clear-parent",
        action="store_true",
        help="Remove parent from this tag.",
    )
    _add_json_argument(tags_update_parser, help_text="Output updated tag as JSON.")

    tags_rename_parser = tags_subparsers.add_parser(
        "rename",
        help="Rename a tag",
    )
    tags_rename_parser.add_argument("old_name", type=str, help="Current tag name")
    tags_rename_parser.add_argument("new_name", type=str, help="New tag name")
    _add_json_argument(tags_rename_parser, help_text="Output result as JSON.")

    tags_delete_parser = tags_subparsers.add_parser(
        "delete",
        help="Delete a tag",
    )
    tags_delete_parser.add_argument("name", type=str, help="Tag name")
    _add_json_argument(tags_delete_parser, help_text="Output result as JSON.")

    tags_merge_parser = tags_subparsers.add_parser(
        "merge",
        help="Merge source tag into target tag",
    )
    tags_merge_parser.add_argument("source", type=str, help="Source tag name")
    tags_merge_parser.add_argument("target", type=str, help="Target tag name")
    _add_json_argument(tags_merge_parser, help_text="Output result as JSON.")

    user_parser = subparsers.add_parser(
        "user",
        help="User/account information",
        description="User profile and account information commands.",
    )
    user_subparsers = user_parser.add_subparsers(
        dest="user_command",
        metavar="<action>",
        required=True,
    )

    user_profile_parser = user_subparsers.add_parser(
        "profile",
        help="Get user profile",
    )
    _add_json_argument(user_profile_parser, help_text="Output profile as JSON.")

    user_status_parser = user_subparsers.add_parser(
        "status",
        help="Get account status/subscription details",
    )
    _add_json_argument(user_status_parser, help_text="Output status as JSON.")

    user_stats_parser = user_subparsers.add_parser(
        "statistics",
        help="Get productivity statistics",
    )
    _add_json_argument(user_stats_parser, help_text="Output statistics as JSON.")

    user_preferences_parser = user_subparsers.add_parser(
        "preferences",
        help="Get user preferences/settings",
    )
    _add_json_argument(user_preferences_parser, help_text="Output preferences as JSON.")

    focus_parser = subparsers.add_parser(
        "focus",
        help="Focus/Pomodoro analytics",
        description="Focus statistics commands.",
    )
    focus_subparsers = focus_parser.add_subparsers(
        dest="focus_command",
        metavar="<action>",
        required=True,
    )

    focus_heatmap_parser = focus_subparsers.add_parser(
        "heatmap",
        help="Get focus heatmap",
    )
    focus_heatmap_parser.add_argument("--from", dest="from_date", type=str, default=None, help="Start date (YYYY-MM-DD).")
    focus_heatmap_parser.add_argument("--to", dest="to_date", type=str, default=None, help="End date (YYYY-MM-DD).")
    focus_heatmap_parser.add_argument("--days", type=int, default=30, help="Days lookback when --from/--to not set.")
    _add_json_argument(focus_heatmap_parser, help_text="Output heatmap data as JSON.")

    focus_by_tag_parser = focus_subparsers.add_parser(
        "by-tag",
        help="Get focus durations grouped by tag",
    )
    focus_by_tag_parser.add_argument("--from", dest="from_date", type=str, default=None, help="Start date (YYYY-MM-DD).")
    focus_by_tag_parser.add_argument("--to", dest="to_date", type=str, default=None, help="End date (YYYY-MM-DD).")
    focus_by_tag_parser.add_argument("--days", type=int, default=30, help="Days lookback when --from/--to not set.")
    _add_json_argument(focus_by_tag_parser, help_text="Output focus-by-tag data as JSON.")

    habits_parser = subparsers.add_parser(
        "habits",
        help="Manage habits",
        description="Habit management and check-in commands.",
    )
    habits_subparsers = habits_parser.add_subparsers(
        dest="habits_command",
        metavar="<action>",
        required=True,
    )

    habits_list_parser = habits_subparsers.add_parser(
        "list",
        help="List habits",
    )
    _add_json_argument(habits_list_parser, help_text="Output habits as JSON.")

    habits_get_parser = habits_subparsers.add_parser(
        "get",
        help="Get habit by ID",
    )
    habits_get_parser.add_argument("habit_id", type=str, help="Habit ID")
    _add_json_argument(habits_get_parser, help_text="Output habit as JSON.")

    habits_sections_parser = habits_subparsers.add_parser(
        "sections",
        help="List habit sections",
    )
    _add_json_argument(habits_sections_parser, help_text="Output sections as JSON.")

    habits_preferences_parser = habits_subparsers.add_parser(
        "preferences",
        help="Get habit preferences",
    )
    _add_json_argument(habits_preferences_parser, help_text="Output preferences as JSON.")

    habits_create_parser = habits_subparsers.add_parser(
        "create",
        help="Create a habit",
    )
    habits_create_parser.add_argument("name", type=str, help="Habit name")
    habits_create_parser.add_argument("--type", dest="habit_type", choices=["Boolean", "Real"], default="Boolean", help="Habit type.")
    habits_create_parser.add_argument("--goal", type=float, default=1.0, help="Goal value.")
    habits_create_parser.add_argument("--step", type=float, default=0.0, help="Step value.")
    habits_create_parser.add_argument("--unit", type=str, default="Count", help="Unit label.")
    habits_create_parser.add_argument("--icon", type=str, default="habit_daily_check_in", help="Habit icon key.")
    habits_create_parser.add_argument("--color", type=str, default="#97E38B", help="Hex color.")
    habits_create_parser.add_argument("--section", dest="section_id", type=str, default=None, help="Section ID.")
    habits_create_parser.add_argument(
        "--repeat",
        dest="repeat_rule",
        type=str,
        default="RRULE:FREQ=WEEKLY;BYDAY=SU,MO,TU,WE,TH,FR,SA",
        help="Repeat rule (RRULE).",
    )
    habits_create_parser.add_argument("--reminders", type=str, default=None, help="Comma-separated reminder times (HH:MM).")
    habits_create_parser.add_argument("--target-days", type=int, default=0, help="Target days.")
    habits_create_parser.add_argument("--encouragement", type=str, default="", help="Encouragement text.")
    _add_json_argument(habits_create_parser, help_text="Output created habit as JSON.")

    habits_update_parser = habits_subparsers.add_parser(
        "update",
        help="Update a habit",
    )
    habits_update_parser.add_argument("habit_id", type=str, help="Habit ID")
    habits_update_parser.add_argument("--name", type=str, default=None, help="New habit name.")
    habits_update_parser.add_argument("--goal", type=float, default=None, help="New goal value.")
    habits_update_parser.add_argument("--step", type=float, default=None, help="New step value.")
    habits_update_parser.add_argument("--unit", type=str, default=None, help="New unit.")
    habits_update_parser.add_argument("--icon", type=str, default=None, help="New icon key.")
    habits_update_parser.add_argument("--color", type=str, default=None, help="New hex color.")
    habits_update_parser.add_argument("--section", dest="section_id", type=str, default=None, help="New section ID.")
    habits_update_parser.add_argument("--repeat", dest="repeat_rule", type=str, default=None, help="New repeat RRULE.")
    habits_update_parser.add_argument("--reminders", type=str, default=None, help="New comma-separated reminder times.")
    habits_update_parser.add_argument("--target-days", type=int, default=None, help="New target days.")
    habits_update_parser.add_argument("--encouragement", type=str, default=None, help="New encouragement text.")
    _add_json_argument(habits_update_parser, help_text="Output updated habit as JSON.")

    habits_delete_parser = habits_subparsers.add_parser(
        "delete",
        help="Delete a habit",
    )
    habits_delete_parser.add_argument("habit_id", type=str, help="Habit ID")
    _add_json_argument(habits_delete_parser, help_text="Output result as JSON.")

    habits_checkin_parser = habits_subparsers.add_parser(
        "checkin",
        help="Check in a habit",
    )
    habits_checkin_parser.add_argument("habit_id", type=str, help="Habit ID")
    habits_checkin_parser.add_argument("--value", type=float, default=1.0, help="Check-in value.")
    habits_checkin_parser.add_argument("--date", dest="checkin_date", type=str, default=None, help="Check-in date (YYYY-MM-DD).")
    _add_json_argument(habits_checkin_parser, help_text="Output updated habit as JSON.")

    habits_batch_checkin_parser = habits_subparsers.add_parser(
        "batch-checkin",
        help="Check in multiple habits from JSON file",
    )
    habits_batch_checkin_parser.add_argument("--file", required=True, help="Path to JSON array of check-ins.")
    _add_json_argument(habits_batch_checkin_parser, help_text="Output batch check-in result as JSON.")

    habits_archive_parser = habits_subparsers.add_parser(
        "archive",
        help="Archive a habit",
    )
    habits_archive_parser.add_argument("habit_id", type=str, help="Habit ID")
    _add_json_argument(habits_archive_parser, help_text="Output updated habit as JSON.")

    habits_unarchive_parser = habits_subparsers.add_parser(
        "unarchive",
        help="Unarchive a habit",
    )
    habits_unarchive_parser.add_argument("habit_id", type=str, help="Habit ID")
    _add_json_argument(habits_unarchive_parser, help_text="Output updated habit as JSON.")

    habits_checkins_parser = habits_subparsers.add_parser(
        "checkins",
        help="Get check-in history for one or more habits",
    )
    habits_checkins_parser.add_argument("habit_ids", nargs="+", help="One or more habit IDs.")
    habits_checkins_parser.add_argument(
        "--after-stamp",
        type=int,
        default=0,
        help="Return check-ins after YYYYMMDD stamp (0 for all).",
    )
    _add_json_argument(habits_checkins_parser, help_text="Output check-ins as JSON.")

    return parser

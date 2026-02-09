"""Command handlers and data formatting for ticktick-cli."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, date, datetime, time, tzinfo
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Tool categories for --enabledModules flag
TOOL_MODULES = {
    "tasks": [
        "ticktick_create_tasks",
        "ticktick_get_task",
        "ticktick_list_tasks",
        "ticktick_update_tasks",
        "ticktick_complete_tasks",
        "ticktick_delete_tasks",
        "ticktick_move_tasks",
        "ticktick_set_task_parents",
        "ticktick_unparent_tasks",
        "ticktick_search_tasks",
        "ticktick_pin_tasks",
    ],
    "projects": [
        "ticktick_list_projects",
        "ticktick_get_project",
        "ticktick_create_project",
        "ticktick_update_project",
        "ticktick_delete_project",
    ],
    "folders": [
        "ticktick_list_folders",
        "ticktick_create_folder",
        "ticktick_rename_folder",
        "ticktick_delete_folder",
    ],
    "columns": [
        "ticktick_list_columns",
        "ticktick_create_column",
        "ticktick_update_column",
        "ticktick_delete_column",
    ],
    "tags": [
        "ticktick_list_tags",
        "ticktick_create_tag",
        "ticktick_update_tag",
        "ticktick_delete_tag",
        "ticktick_merge_tags",
    ],
    "habits": [
        "ticktick_habits",
        "ticktick_habit",
        "ticktick_habit_sections",
        "ticktick_create_habit",
        "ticktick_update_habit",
        "ticktick_delete_habit",
        "ticktick_checkin_habits",
        "ticktick_habit_checkins",
    ],
    "user": [
        "ticktick_get_profile",
        "ticktick_get_status",
        "ticktick_get_statistics",
        "ticktick_get_preferences",
    ],
    "focus": [
        "ticktick_focus_heatmap",
        "ticktick_focus_by_tag",
    ],
}

ALL_TOOLS = [tool for tools in TOOL_MODULES.values() for tool in tools]

_AUTH_FIX_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
_AUTH_FIX_WEB_APP_VERSION = 6430


def _resolve_auth_host() -> str:
    host = os.environ.get("TICKTICK_HOST", "ticktick.com").lower().strip()
    if host in ("ticktick.com", "dida365.com"):
        return host
    return "ticktick.com"


def _patch_v2_session_handler_for_429(session_handler_cls: type[Any]) -> bool:
    """Patch older SDK SessionHandler to avoid V2 signon 429 responses."""
    if getattr(session_handler_cls, "_ticktick_cli_429_fix_applied", False):
        return False

    try:
        probe = session_handler_cls(device_id="0" * 24)
        headers = probe._get_headers()
        if "Origin" in headers and "Referer" in headers:
            setattr(session_handler_cls, "_ticktick_cli_429_fix_applied", True)
            return False
    except Exception:
        pass

    def _get_x_device_header(self: Any) -> str:
        version = getattr(self, "WEB_APP_VERSION", _AUTH_FIX_WEB_APP_VERSION)
        return json.dumps(
            {
                "platform": "web",
                "os": "macOS 10.15.7",
                "device": "Chrome 120.0.0.0",
                "name": "",
                "version": version,
                "id": getattr(self, "device_id", ""),
                "channel": "website",
                "campaign": "",
                "websocket": "",
            }
        )

    def _get_headers(self: Any) -> dict[str, str]:
        host = _resolve_auth_host()
        origin = f"https://{host}"
        return {
            "User-Agent": getattr(self, "DEFAULT_USER_AGENT", _AUTH_FIX_USER_AGENT),
            "Origin": origin,
            "Referer": f"{origin}/",
            "X-Device": self._get_x_device_header(),
        }

    if not hasattr(session_handler_cls, "WEB_APP_VERSION"):
        setattr(session_handler_cls, "WEB_APP_VERSION", _AUTH_FIX_WEB_APP_VERSION)

    setattr(session_handler_cls, "DEFAULT_USER_AGENT", _AUTH_FIX_USER_AGENT)
    setattr(session_handler_cls, "_get_x_device_header", _get_x_device_header)
    setattr(session_handler_cls, "_get_headers", _get_headers)
    setattr(session_handler_cls, "_ticktick_cli_429_fix_applied", True)
    return True


def _apply_v2_auth_rate_limit_workaround() -> None:
    """Apply SDK compatibility fix for auth headers until upstream release.

    TODO: Remove this workaround after ticktick-sdk ships the PR #34 auth fix
    in a stable release and this CLI bumps its minimum required SDK version.
    """
    try:
        from ticktick_sdk.api.v2.auth import SessionHandler
    except Exception:
        return

    _patch_v2_session_handler_for_429(SessionHandler)


def resolve_enabled_tools(
    enabled_tools: str | None,
    enabled_modules: str | None,
) -> list[str] | None:
    """Resolve enabled tools from CLI arguments."""
    if not enabled_tools and not enabled_modules:
        return None

    result: set[str] = set()

    if enabled_tools:
        for tool in enabled_tools.split(","):
            tool = tool.strip()
            if tool:
                if tool not in ALL_TOOLS:
                    print(f"Warning: Unknown tool '{tool}', skipping", file=sys.stderr)
                else:
                    result.add(tool)

    if enabled_modules:
        for module in enabled_modules.split(","):
            module = module.strip().lower()
            if module:
                if module not in TOOL_MODULES:
                    print(
                        f"Warning: Unknown module '{module}'. "
                        f"Available: {', '.join(TOOL_MODULES.keys())}",
                        file=sys.stderr,
                    )
                else:
                    result.update(TOOL_MODULES[module])

    return list(result) if result else None


def run_server(
    enabled_tools: str | None = None,
    enabled_modules: str | None = None,
    host: str | None = None,
    output_json: bool = False,
) -> int:
    """Run the MCP server."""
    del output_json

    if host:
        host_lower = host.lower().strip()
        if host_lower in ("ticktick.com", "dida365.com"):
            os.environ["TICKTICK_HOST"] = host_lower
            print(f"Using API host: {host_lower}", file=sys.stderr)
        else:
            print(
                f"Warning: Invalid host '{host}'. "
                "Using default (ticktick.com). Valid: ticktick.com, dida365.com",
                file=sys.stderr,
            )

    tools_to_enable = resolve_enabled_tools(enabled_tools, enabled_modules)

    if tools_to_enable is not None:
        os.environ["TICKTICK_ENABLED_TOOLS"] = ",".join(tools_to_enable)
        print(
            f"Tool filtering enabled: {len(tools_to_enable)} of {len(ALL_TOOLS)} tools",
            file=sys.stderr,
        )

    _apply_v2_auth_rate_limit_workaround()

    from ticktick_sdk.server import main as server_main

    server_main()
    return 0


def run_auth(manual: bool = False, output_json: bool = False) -> int:
    """Run the OAuth2 authentication flow."""
    del output_json

    from ticktick_sdk.auth_cli import main as auth_main

    return auth_main(manual=manual)


def _priority_label(priority: int) -> str:
    labels = {0: "none", 1: "low", 3: "medium", 5: "high"}
    return labels.get(priority, str(priority))


def _status_label(status: int) -> str:
    labels = {-1: "abandoned", 0: "active", 1: "completed", 2: "completed"}
    return labels.get(status, f"unknown({status})")


def _print_json(payload: dict[str, Any]) -> None:
    # Preserve non-ASCII characters (e.g., Cyrillic task titles) in CLI output.
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    if max_length <= 3:
        return value[:max_length]
    return value[: max_length - 3] + "..."


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [len(h) for h in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def _format_row(row_values: list[str]) -> str:
        padded = [value.ljust(widths[i]) for i, value in enumerate(row_values)]
        return "  ".join(padded)

    print(_format_row(headers))
    print(_format_row(["-" * width for width in widths]))
    for row in rows:
        print(_format_row(row))


def _datetime_in_timezone(value: datetime, tz: tzinfo) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(tz)


def _task_due_as_local_date(task_due: datetime | None, tz: tzinfo) -> date | None:
    if task_due is None:
        return None
    return _datetime_in_timezone(task_due, tz).date()


def _format_due(task_due: datetime | None, tz: tzinfo) -> str:
    if task_due is None:
        return "-"
    local_due = _datetime_in_timezone(task_due, tz)
    return local_due.strftime("%Y-%m-%d %H:%M")


def _get_cli_timezone() -> tuple[tzinfo, str | None]:
    tz_name = os.environ.get("TZ")
    if tz_name:
        try:
            return ZoneInfo(tz_name), tz_name
        except ZoneInfoNotFoundError as exc:
            raise ValueError(
                f"Invalid TZ value '{tz_name}'. Use an IANA timezone like 'America/New_York'."
            ) from exc

    local_timezone = datetime.now().astimezone().tzinfo
    if local_timezone is None:
        return UTC, None
    return local_timezone, None


def _timezone_name_for_task(tz: tzinfo, configured_name: str | None) -> str | None:
    if configured_name:
        return configured_name
    if isinstance(tz, ZoneInfo):
        return tz.key
    return None


def _parse_due_filter(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Invalid --due value '{value}'. Expected YYYY-MM-DD.") from exc


def _parse_due_for_creation(value: str, tz: tzinfo) -> tuple[datetime, bool]:
    try:
        due_day = date.fromisoformat(value)
        return datetime.combine(due_day, time.min, tz), True
    except ValueError:
        pass

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid --due value '{value}'. Use YYYY-MM-DD or ISO datetime."
        ) from exc

    parsed = parsed.replace(tzinfo=tz) if parsed.tzinfo is None else parsed.astimezone(tz)
    return parsed, False


def _task_to_json(task: Any, tz: tzinfo) -> dict[str, Any]:
    due_date = getattr(task, "due_date", None)
    due_local = _datetime_in_timezone(due_date, tz) if due_date else None
    status = int(getattr(task, "status", 0))
    priority = int(getattr(task, "priority", 0))
    return {
        "id": getattr(task, "id", None),
        "project_id": getattr(task, "project_id", None),
        "title": getattr(task, "title", None),
        "content": getattr(task, "content", None),
        "description": getattr(task, "desc", None),
        "status": status,
        "status_label": _status_label(status),
        "priority": priority,
        "priority_label": _priority_label(priority),
        "due_date": due_date.isoformat() if due_date else None,
        "due_local": due_local.isoformat() if due_local else None,
        "tags": list(getattr(task, "tags", []) or []),
        "is_all_day": getattr(task, "is_all_day", None),
    }


def _project_to_json(project: Any, current_project_id: str) -> dict[str, Any]:
    project_id = getattr(project, "id", "")
    return {
        "id": project_id,
        "name": getattr(project, "name", ""),
        "kind": getattr(project, "kind", None),
        "view_mode": getattr(project, "view_mode", None),
        "closed": bool(getattr(project, "closed", False)),
        "is_current": project_id == current_project_id,
    }


def _print_task_list_pretty(
    tasks: list[Any],
    project_id: str,
    due_filter: date | None,
    tz_name: str,
    tz: tzinfo,
) -> None:
    filters = [f"project={project_id}"]
    if due_filter is not None:
        filters.append(f"due={due_filter.isoformat()}")
    filters.append(f"tz={tz_name}")

    print(f"Tasks ({len(tasks)})")
    print(f"Filters: {', '.join(filters)}")

    if not tasks:
        print("No tasks found.")
        return

    rows: list[list[str]] = []
    for task in tasks:
        title = getattr(task, "title", None) or "(no title)"
        due_date = getattr(task, "due_date", None)
        priority = int(getattr(task, "priority", 0))
        status = int(getattr(task, "status", 0))
        rows.append([
            str(getattr(task, "id", "")),
            _truncate(title, 48),
            _format_due(due_date, tz),
            _priority_label(priority),
            _status_label(status),
        ])

    _print_table(["ID", "Title", "Due", "Priority", "Status"], rows)


def _print_created_task_pretty(task: Any, tz: tzinfo) -> None:
    print("Task created")
    rows = [[
        str(getattr(task, "id", "")),
        getattr(task, "title", None) or "(no title)",
        _format_due(getattr(task, "due_date", None), tz),
        _priority_label(int(getattr(task, "priority", 0))),
    ]]
    _print_table(["ID", "Title", "Due", "Priority"], rows)


def _print_projects_pretty(projects: list[Any], current_project_id: str) -> None:
    print(f"Projects ({len(projects)})")

    if not projects:
        print("No projects found.")
        return

    rows: list[list[str]] = []
    for project in projects:
        project_id = str(getattr(project, "id", ""))
        name = str(getattr(project, "name", ""))
        rows.append([
            "*" if project_id == current_project_id else "",
            project_id,
            _truncate(name, 36),
            str(getattr(project, "kind", "TASK") or "TASK"),
            str(getattr(project, "view_mode", "list") or "list"),
            "yes" if bool(getattr(project, "closed", False)) else "no",
        ])

    _print_table(["Current", "ID", "Name", "Kind", "View", "Closed"], rows)


def _task_sort_key(task: Any, tz: tzinfo) -> tuple[bool, str, int, str]:
    due_date = getattr(task, "due_date", None)
    due_local = _datetime_in_timezone(due_date, tz) if due_date else None
    due_sort = due_local.isoformat() if due_local else "9999-12-31T23:59:59+00:00"
    priority = int(getattr(task, "priority", 0))
    title = str(getattr(task, "title", "") or "")
    return (due_local is None, due_sort, -priority, title.casefold())


async def _resolve_project_id(client: Any, explicit_project_id: str | None) -> str:
    if explicit_project_id:
        return explicit_project_id

    configured_project = os.environ.get("TICKTICK_CURRENT_PROJECT_ID", "").strip()
    if configured_project:
        return configured_project

    inbox_id = getattr(client, "inbox_id", None)
    if inbox_id:
        return str(inbox_id)

    status = await client.get_status()
    return str(status.inbox_id)


async def _resolve_task_project_id(
    client: Any,
    task_id: str,
    explicit_project_id: str | None,
) -> str:
    if explicit_project_id:
        return explicit_project_id

    task = await client.get_task(task_id)
    return str(task.project_id)


async def _abandon_task(client: Any, task_id: str, project_id: str) -> None:
    """Abandon task with backward-compatible fallback for older SDK versions."""
    abandon_method = getattr(client, "abandon_task", None)
    if callable(abandon_method):
        await abandon_method(task_id, project_id)
        return

    update_method = getattr(client, "update_task", None)
    if not callable(update_method):
        raise ValueError(
            "Installed ticktick-sdk does not support abandon_task and has no update_task fallback."
        )

    from ticktick_sdk.constants import TaskStatus

    task = await client.get_task(task_id, project_id)
    task.status = int(TaskStatus.ABANDONED)
    task.completed_time = datetime.now(UTC)
    await update_method(task)


async def _run_tasks_command(client: Any, args: argparse.Namespace) -> int:
    tz, configured_tz_name = _get_cli_timezone()
    tz_display_name = configured_tz_name or "local"

    if args.tasks_command == "list":
        project_id = await _resolve_project_id(client, args.project_id)
        tasks = await client.get_all_tasks()
        filtered = [task for task in tasks if str(getattr(task, "project_id", "")) == project_id]

        due_filter: date | None = None
        if args.due:
            due_filter = _parse_due_filter(args.due)
            filtered = [
                task for task in filtered
                if _task_due_as_local_date(getattr(task, "due_date", None), tz) == due_filter
            ]

        filtered.sort(key=lambda task: _task_sort_key(task, tz))

        if args.json:
            payload = {
                "count": len(filtered),
                "project_id": project_id,
                "timezone": tz_display_name,
                "filters": {
                    "due": due_filter.isoformat() if due_filter else None,
                },
                "tasks": [_task_to_json(task, tz) for task in filtered],
            }
            _print_json(payload)
        else:
            _print_task_list_pretty(filtered, project_id, due_filter, tz_display_name, tz)

        return 0

    if args.tasks_command == "add":
        project_id = await _resolve_project_id(client, args.project_id)

        due_date: datetime | None = None
        all_day: bool | None = None
        task_timezone = _timezone_name_for_task(tz, configured_tz_name)

        if args.due:
            due_date, all_day = _parse_due_for_creation(args.due, tz)

        created = await client.create_task(
            title=args.title,
            project_id=project_id,
            content=args.content,
            due_date=due_date,
            all_day=all_day,
            time_zone=task_timezone,
            priority=args.priority,
        )

        if args.json:
            payload = {
                "success": True,
                "task": _task_to_json(created, tz),
            }
            _print_json(payload)
        else:
            _print_created_task_pretty(created, tz)

        return 0

    if args.tasks_command == "done":
        project_id = await _resolve_task_project_id(client, args.task_id, args.project_id)
        await client.complete_task(args.task_id, project_id)

        if args.json:
            payload = {
                "success": True,
                "action": "done",
                "task_id": args.task_id,
                "project_id": project_id,
            }
            _print_json(payload)
        else:
            print(f"Task {args.task_id} marked as completed.")

        return 0

    if args.tasks_command == "abandon":
        project_id = await _resolve_task_project_id(client, args.task_id, args.project_id)
        await _abandon_task(client, args.task_id, project_id)

        if args.json:
            payload = {
                "success": True,
                "action": "abandon",
                "task_id": args.task_id,
                "project_id": project_id,
            }
            _print_json(payload)
        else:
            print(f"Task {args.task_id} marked as abandoned (won't do).")

        return 0

    raise ValueError(f"Unknown tasks subcommand: {args.tasks_command}")


async def _run_projects_command(client: Any, args: argparse.Namespace) -> int:
    if args.projects_command != "list":
        raise ValueError(f"Unknown projects subcommand: {args.projects_command}")

    projects = await client.get_all_projects()
    projects_sorted = sorted(projects, key=lambda project: str(project.name).casefold())
    current_project_id = await _resolve_project_id(client, None)

    if args.json:
        payload = {
            "count": len(projects_sorted),
            "current_project_id": current_project_id,
            "projects": [
                _project_to_json(project, current_project_id)
                for project in projects_sorted
            ],
        }
        _print_json(payload)
    else:
        _print_projects_pretty(projects_sorted, current_project_id)

    return 0


async def run_data_cli(args: argparse.Namespace) -> int:
    """Run task/project CLI commands."""
    _apply_v2_auth_rate_limit_workaround()

    from ticktick_sdk.client import TickTickClient
    from ticktick_sdk.exceptions import TickTickConfigurationError, TickTickError

    try:
        async with TickTickClient.from_settings() as client:
            if args.command == "tasks":
                return await _run_tasks_command(client, args)
            if args.command == "projects":
                return await _run_projects_command(client, args)

            raise ValueError(f"Unsupported command for data CLI: {args.command}")

    except TickTickConfigurationError as exc:
        message = getattr(exc, "message", str(exc))
        print(f"Configuration error: {message}", file=sys.stderr)
        missing_config = getattr(exc, "missing_config", None)
        if missing_config:
            missing = ", ".join(missing_config)
            print(f"Missing environment variables: {missing}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except TickTickError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

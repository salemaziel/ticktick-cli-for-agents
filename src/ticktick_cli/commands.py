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


def _parse_csv_list(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",")]
    result = [item for item in items if item]
    return result or []


def _parse_priority_value(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    normalized = value.strip().lower()
    mapping = {"none": 0, "low": 1, "medium": 3, "high": 5}
    if normalized in mapping:
        return mapping[normalized]
    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise ValueError(
            f"Invalid priority '{value}'. Use none/low/medium/high or 0/1/3/5."
        ) from exc
    if parsed not in {0, 1, 3, 5}:
        raise ValueError(
            f"Invalid priority '{value}'. Use none/low/medium/high or 0/1/3/5."
        )
    return parsed


def _load_json_array_from_file(path: str) -> list[Any]:
    try:
        with open(path, encoding="utf-8") as file:
            payload = json.load(file)
    except FileNotFoundError as exc:
        raise ValueError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in file '{path}': {exc}") from exc

    if not isinstance(payload, list):
        raise ValueError(f"Expected JSON array in file '{path}'.")
    return payload


def _filter_tasks_by_project(tasks: list[Any], project_id: str | None) -> list[Any]:
    if not project_id:
        return tasks
    return [task for task in tasks if str(getattr(task, "project_id", "")) == project_id]


def _print_task_details_pretty(task: Any, tz: tzinfo) -> None:
    due_date = getattr(task, "due_date", None)
    start_date = getattr(task, "start_date", None)
    tags = list(getattr(task, "tags", []) or [])

    print("Task")
    print(f"ID: {getattr(task, 'id', '')}")
    print(f"Project: {getattr(task, 'project_id', '')}")
    print(f"Title: {getattr(task, 'title', '') or '(no title)'}")
    print(f"Status: {_status_label(int(getattr(task, 'status', 0)))}")
    print(f"Priority: {_priority_label(int(getattr(task, 'priority', 0)))}")
    print(f"Start: {_format_due(start_date, tz)}")
    print(f"Due: {_format_due(due_date, tz)}")
    print(f"Pinned: {'yes' if getattr(task, 'pinned_time', None) else 'no'}")
    if tags:
        print(f"Tags: {', '.join(tags)}")
    content = getattr(task, "content", None)
    if content:
        print(f"Content: {content}")
    description = getattr(task, "desc", None)
    if description:
        print(f"Description: {description}")


def _print_batch_result_pretty(action: str, response: Any) -> None:
    if isinstance(response, dict):
        id2etag = response.get("id2etag", {}) or {}
        id2error = response.get("id2error", {}) or {}
        print(f"{action}: {len(id2etag)} succeeded, {len(id2error)} failed")
        if id2error:
            for task_id, error in id2error.items():
                print(f"- {task_id}: {error}")
        return

    if isinstance(response, list):
        print(f"{action}: processed {len(response)} item(s).")
        return

    print(f"{action}: done")


def _task_to_json(task: Any, tz: tzinfo) -> dict[str, Any]:
    start_date = getattr(task, "start_date", None)
    start_local = _datetime_in_timezone(start_date, tz) if start_date else None
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
        "kind": getattr(task, "kind", None),
        "status": status,
        "status_label": _status_label(status),
        "priority": priority,
        "priority_label": _priority_label(priority),
        "start_date": start_date.isoformat() if start_date else None,
        "start_local": start_local.isoformat() if start_local else None,
        "due_date": due_date.isoformat() if due_date else None,
        "due_local": due_local.isoformat() if due_local else None,
        "tags": list(getattr(task, "tags", []) or []),
        "parent_id": getattr(task, "parent_id", None),
        "column_id": getattr(task, "column_id", None),
        "time_zone": getattr(task, "time_zone", None),
        "pinned_time": (
            getattr(task, "pinned_time", None).isoformat()
            if getattr(task, "pinned_time", None) is not None
            else None
        ),
        "is_all_day": getattr(task, "is_all_day", None),
    }


def _project_to_json(project: Any, current_project_id: str) -> dict[str, Any]:
    project_id = getattr(project, "id", "")
    return {
        "id": project_id,
        "name": getattr(project, "name", ""),
        "color": getattr(project, "color", None),
        "folder_id": getattr(project, "group_id", None),
        "kind": getattr(project, "kind", None),
        "view_mode": getattr(project, "view_mode", None),
        "sort_option": getattr(project, "sort_option", None),
        "sort_order": getattr(project, "sort_order", None),
        "sort_type": getattr(project, "sort_type", None),
        "closed": bool(getattr(project, "closed", False)),
        "muted": bool(getattr(project, "muted", False)),
        "permission": getattr(project, "permission", None),
        "is_current": project_id == current_project_id,
    }


def _column_to_json(column: Any) -> dict[str, Any]:
    return {
        "id": getattr(column, "id", None),
        "project_id": getattr(column, "project_id", None),
        "name": getattr(column, "name", None),
        "sort_order": getattr(column, "sort_order", None),
        "created_time": (
            getattr(column, "created_time", None).isoformat()
            if getattr(column, "created_time", None) is not None
            else None
        ),
        "modified_time": (
            getattr(column, "modified_time", None).isoformat()
            if getattr(column, "modified_time", None) is not None
            else None
        ),
    }


def _project_data_to_json(project_data: Any, current_project_id: str, tz: tzinfo) -> dict[str, Any]:
    project = getattr(project_data, "project", None)
    tasks = list(getattr(project_data, "tasks", []) or [])
    columns = list(getattr(project_data, "columns", []) or [])
    tasks_sorted = sorted(tasks, key=lambda task: _task_sort_key(task, tz))
    return {
        "project": _project_to_json(project, current_project_id) if project else None,
        "task_count": len(tasks_sorted),
        "column_count": len(columns),
        "tasks": [_task_to_json(task, tz) for task in tasks_sorted],
        "columns": [_column_to_json(column) for column in columns],
    }


def _print_task_list_pretty(
    tasks: list[Any],
    project_id: str | None,
    due_filter: date | None,
    tz_name: str,
    tz: tzinfo,
    *,
    title: str = "Tasks",
    show_project: bool = False,
) -> None:
    filters: list[str] = []
    if project_id:
        filters.append(f"project={project_id}")
    if due_filter is not None:
        filters.append(f"due={due_filter.isoformat()}")
    filters.append(f"tz={tz_name}")

    print(f"{title} ({len(tasks)})")
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
        row = [
            str(getattr(task, "id", "")),
            _truncate(title, 48),
            _format_due(due_date, tz),
            _priority_label(priority),
            _status_label(status),
        ]
        if show_project:
            row.insert(1, str(getattr(task, "project_id", "")))
        rows.append(row)

    headers = ["ID", "Title", "Due", "Priority", "Status"]
    if show_project:
        headers.insert(1, "Project")
    _print_table(headers, rows)


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


def _print_project_details_pretty(project: Any, current_project_id: str) -> None:
    project_id = str(getattr(project, "id", ""))
    print("Project")
    print(f"ID: {project_id}")
    print(f"Name: {getattr(project, 'name', '')}")
    print(f"Current: {'yes' if project_id == current_project_id else 'no'}")
    print(f"Kind: {getattr(project, 'kind', '')}")
    print(f"View: {getattr(project, 'view_mode', '')}")
    print(f"Color: {getattr(project, 'color', '') or '-'}")
    print(f"Folder ID: {getattr(project, 'group_id', '') or '-'}")
    print(f"Closed: {'yes' if bool(getattr(project, 'closed', False)) else 'no'}")
    print(f"Muted: {'yes' if bool(getattr(project, 'muted', False)) else 'no'}")
    print(f"Permission: {getattr(project, 'permission', '') or '-'}")


def _print_project_data_pretty(
    project_data: Any,
    current_project_id: str,
    tz: tzinfo,
    tz_name: str,
) -> None:
    project = getattr(project_data, "project", None)
    tasks = list(getattr(project_data, "tasks", []) or [])
    columns = list(getattr(project_data, "columns", []) or [])

    if project is not None:
        _print_project_details_pretty(project, current_project_id)
        print()

    tasks_sorted = sorted(tasks, key=lambda task: _task_sort_key(task, tz))
    _print_task_list_pretty(
        tasks_sorted,
        str(getattr(project, "id", "")) if project is not None else None,
        None,
        tz_name,
        tz,
        title="Project Tasks",
        show_project=False,
    )

    print()
    print(f"Columns ({len(columns)})")
    if not columns:
        print("No columns found.")
        return

    rows: list[list[str]] = []
    for column in columns:
        rows.append([
            str(getattr(column, "id", "")),
            str(getattr(column, "name", "") or ""),
            str(getattr(column, "sort_order", "") or ""),
        ])
    _print_table(["ID", "Name", "Sort"], rows)


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
    json_output = bool(getattr(args, "json", False))

    if args.tasks_command == "list":
        project_id = await _resolve_project_id(client, getattr(args, "project_id", None))
        tasks = await client.get_all_tasks()
        filtered = _filter_tasks_by_project(tasks, project_id)

        due_filter: date | None = None
        if getattr(args, "due", None):
            due_filter = _parse_due_filter(args.due)
            filtered = [
                task for task in filtered
                if _task_due_as_local_date(getattr(task, "due_date", None), tz) == due_filter
            ]

        filtered.sort(key=lambda task: _task_sort_key(task, tz))

        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "timezone": tz_display_name,
                "filters": {
                    "due": due_filter.isoformat() if due_filter else None,
                },
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(filtered, project_id, due_filter, tz_display_name, tz)

        return 0

    if args.tasks_command == "get":
        task_id = getattr(args, "task_id")
        project_id = getattr(args, "project_id", None)
        task = await client.get_task(task_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "task": _task_to_json(task, tz),
            })
        else:
            _print_task_details_pretty(task, tz)
        return 0

    if args.tasks_command == "add":
        project_id = await _resolve_project_id(client, getattr(args, "project_id", None))
        task_timezone = getattr(args, "time_zone", None) or _timezone_name_for_task(
            tz,
            configured_tz_name,
        )
        due_date: datetime | None = None
        start_date: datetime | None = None
        all_day: bool | None = None

        if getattr(args, "start", None):
            start_date, _ = _parse_due_for_creation(args.start, tz)
        if getattr(args, "due", None):
            due_date, all_day = _parse_due_for_creation(args.due, tz)
        if getattr(args, "all_day", False):
            all_day = True
        if getattr(args, "timed", False):
            all_day = False

        tags = _parse_csv_list(getattr(args, "tags", None))
        reminders = _parse_csv_list(getattr(args, "reminders", None))
        kind = getattr(args, "kind", None)
        normalized_kind = kind.upper() if isinstance(kind, str) else None

        created = await client.create_task(
            title=args.title,
            project_id=project_id,
            content=getattr(args, "content", None),
            description=getattr(args, "description", None),
            priority=getattr(args, "priority", None),
            start_date=start_date,
            due_date=due_date,
            time_zone=task_timezone,
            all_day=all_day,
            reminders=reminders,
            recurrence=getattr(args, "recurrence", None),
            tags=tags,
            parent_id=getattr(args, "parent_id", None),
        )

        if normalized_kind is not None and getattr(created, "kind", None) != normalized_kind:
            created.kind = normalized_kind
            created = await client.update_task(created)

        if json_output:
            _print_json({
                "success": True,
                "task": _task_to_json(created, tz),
            })
        else:
            _print_created_task_pretty(created, tz)
        return 0

    if args.tasks_command == "quick-add":
        project_id = await _resolve_project_id(client, getattr(args, "project_id", None))
        created = await client.quick_add(args.text, project_id)
        if json_output:
            _print_json({
                "success": True,
                "task": _task_to_json(created, tz),
            })
        else:
            _print_created_task_pretty(created, tz)
        return 0

    if args.tasks_command == "update":
        if getattr(args, "start", None) and getattr(args, "clear_start", False):
            raise ValueError("Use either --start or --clear-start, not both.")
        if getattr(args, "due", None) and getattr(args, "clear_due", False):
            raise ValueError("Use either --due or --clear-due, not both.")
        if getattr(args, "tags", None) and getattr(args, "clear_tags", False):
            raise ValueError("Use either --tags or --clear-tags, not both.")
        if getattr(args, "recurrence", None) and getattr(args, "clear_recurrence", False):
            raise ValueError("Use either --recurrence or --clear-recurrence, not both.")

        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        task = await client.get_task(args.task_id, project_id)
        explicit_time_zone = getattr(args, "time_zone", None)
        task_timezone = explicit_time_zone or _timezone_name_for_task(
            tz,
            configured_tz_name,
        )

        changed = False
        if getattr(args, "title", None) is not None:
            task.title = args.title
            changed = True
        if getattr(args, "content", None) is not None:
            task.content = args.content
            changed = True
        if getattr(args, "description", None) is not None:
            task.desc = args.description
            changed = True
        if getattr(args, "kind", None) is not None:
            task.kind = args.kind.upper()
            changed = True
        if getattr(args, "priority", None) is not None:
            task.priority = _parse_priority_value(args.priority)
            changed = True

        if getattr(args, "start", None):
            start_date, _ = _parse_due_for_creation(args.start, tz)
            task.start_date = start_date
            changed = True
        if getattr(args, "clear_start", False):
            task.start_date = None
            changed = True

        if getattr(args, "due", None):
            due_date, all_day = _parse_due_for_creation(args.due, tz)
            task.due_date = due_date
            task.is_all_day = all_day
            if task_timezone:
                task.time_zone = task_timezone
            changed = True
        if getattr(args, "clear_due", False):
            task.due_date = None
            task.is_all_day = None
            changed = True

        if getattr(args, "all_day", False):
            task.is_all_day = True
            changed = True
        if getattr(args, "timed", False):
            task.is_all_day = False
            changed = True

        if getattr(args, "tags", None) is not None:
            task.tags = _parse_csv_list(args.tags) or []
            changed = True
        if getattr(args, "clear_tags", False):
            task.tags = []
            changed = True

        if getattr(args, "recurrence", None) is not None:
            task.repeat_flag = args.recurrence
            changed = True
        if getattr(args, "clear_recurrence", False):
            task.repeat_flag = None
            changed = True

        if explicit_time_zone is not None:
            task.time_zone = explicit_time_zone
            changed = True

        if not changed:
            raise ValueError("No update fields provided.")

        updated = await client.update_task(task)
        if json_output:
            _print_json({
                "success": True,
                "task": _task_to_json(updated, tz),
            })
        else:
            print(f"Task {args.task_id} updated.")
            _print_task_details_pretty(updated, tz)
        return 0

    if args.tasks_command == "done":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        await client.complete_task(args.task_id, project_id)

        if json_output:
            _print_json({
                "success": True,
                "action": "done",
                "task_id": args.task_id,
                "project_id": project_id,
            })
        else:
            print(f"Task {args.task_id} marked as completed.")
        return 0

    if args.tasks_command == "abandon":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        await _abandon_task(client, args.task_id, project_id)

        if json_output:
            _print_json({
                "success": True,
                "action": "abandon",
                "task_id": args.task_id,
                "project_id": project_id,
            })
        else:
            print(f"Task {args.task_id} marked as abandoned (won't do).")
        return 0

    if args.tasks_command == "delete":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        await client.delete_task(args.task_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "delete",
                "task_id": args.task_id,
                "project_id": project_id,
            })
        else:
            print(f"Task {args.task_id} deleted.")
        return 0

    if args.tasks_command == "move":
        from_project_id = getattr(args, "from_project_id", None)
        if not from_project_id:
            from_project_id = await _resolve_task_project_id(client, args.task_id, None)
        to_project_id = args.to_project_id
        await client.move_task(args.task_id, from_project_id, to_project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "move",
                "task_id": args.task_id,
                "from_project_id": from_project_id,
                "to_project_id": to_project_id,
            })
        else:
            print(f"Task {args.task_id} moved from {from_project_id} to {to_project_id}.")
        return 0

    if args.tasks_command == "subtask":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        await client.make_subtask(args.task_id, args.parent_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "subtask",
                "task_id": args.task_id,
                "project_id": project_id,
                "parent_id": args.parent_id,
            })
        else:
            print(f"Task {args.task_id} is now a subtask of {args.parent_id}.")
        return 0

    if args.tasks_command == "unparent":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        await client.unparent_subtask(args.task_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "unparent",
                "task_id": args.task_id,
                "project_id": project_id,
            })
        else:
            print(f"Task {args.task_id} moved to top level.")
        return 0

    if args.tasks_command == "pin":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        task = await client.pin_task(args.task_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "pin",
                "task": _task_to_json(task, tz),
            })
        else:
            print(f"Task {args.task_id} pinned.")
            _print_task_details_pretty(task, tz)
        return 0

    if args.tasks_command == "unpin":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        task = await client.unpin_task(args.task_id, project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "unpin",
                "task": _task_to_json(task, tz),
            })
        else:
            print(f"Task {args.task_id} unpinned.")
            _print_task_details_pretty(task, tz)
        return 0

    if args.tasks_command == "column":
        project_id = await _resolve_task_project_id(client, args.task_id, getattr(args, "project_id", None))
        column_id = None if getattr(args, "clear_column", False) else getattr(args, "column_id", None)
        task = await client.move_task_to_column(args.task_id, project_id, column_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "column",
                "task": _task_to_json(task, tz),
            })
        else:
            if column_id:
                print(f"Task {args.task_id} moved to column {column_id}.")
            else:
                print(f"Task {args.task_id} removed from column.")
            _print_task_details_pretty(task, tz)
        return 0

    if args.tasks_command == "search":
        tasks = await client.search_tasks(args.query)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "query": args.query,
                "project_id": project_id,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title=f"Search: {args.query}",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "by-tag":
        tasks = await client.get_tasks_by_tag(args.tag_name)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "tag": args.tag_name,
                "project_id": project_id,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title=f"Tasks tagged '{args.tag_name}'",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "by-priority":
        priority_value = _parse_priority_value(args.priority)
        if priority_value is None:
            raise ValueError("Priority is required.")
        tasks = await client.get_tasks_by_priority(priority_value)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "priority": priority_value,
                "priority_label": _priority_label(priority_value),
                "project_id": project_id,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title=f"Tasks with priority {_priority_label(priority_value)}",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "today":
        tasks = await client.get_today_tasks()
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                datetime.now(tz).date(),
                tz_display_name,
                tz,
                title="Today's tasks",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "overdue":
        tasks = await client.get_overdue_tasks()
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title="Overdue tasks",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "completed":
        tasks = await client.get_completed_tasks(days=args.days, limit=args.limit)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "days": args.days,
                "limit": args.limit,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title=f"Completed tasks (last {args.days} days)",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "abandoned":
        tasks = await client.get_abandoned_tasks(days=args.days, limit=args.limit)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "days": args.days,
                "limit": args.limit,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title=f"Abandoned tasks (last {args.days} days)",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "deleted":
        tasks = await client.get_deleted_tasks(limit=args.limit)
        project_id = getattr(args, "project_id", None)
        filtered = _filter_tasks_by_project(tasks, project_id)
        filtered.sort(key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "count": len(filtered),
                "project_id": project_id,
                "limit": args.limit,
                "timezone": tz_display_name,
                "tasks": [_task_to_json(task, tz) for task in filtered],
            })
        else:
            _print_task_list_pretty(
                filtered,
                project_id,
                None,
                tz_display_name,
                tz,
                title="Deleted tasks",
                show_project=project_id is None,
            )
        return 0

    if args.tasks_command == "batch-create":
        task_specs = _load_json_array_from_file(args.file)
        created = await client.create_tasks(task_specs)
        created_sorted = sorted(created, key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "success": True,
                "count": len(created_sorted),
                "tasks": [_task_to_json(task, tz) for task in created_sorted],
            })
        else:
            _print_task_list_pretty(
                created_sorted,
                None,
                None,
                tz_display_name,
                tz,
                title="Batch created tasks",
                show_project=True,
            )
        return 0

    if args.tasks_command == "batch-update":
        updates = _load_json_array_from_file(args.file)
        response = await client.update_tasks(updates)
        if json_output:
            _print_json({
                "success": True,
                "action": "batch-update",
                "result": response,
            })
        else:
            _print_batch_result_pretty("batch-update", response)
        return 0

    if args.tasks_command in {"batch-delete", "batch-done"}:
        entries = _load_json_array_from_file(args.file)
        task_ids: list[tuple[str, str]] = []
        for index, entry in enumerate(entries):
            if isinstance(entry, list | tuple) and len(entry) == 2:
                task_ids.append((str(entry[0]), str(entry[1])))
                continue
            if isinstance(entry, dict) and {"task_id", "project_id"} <= set(entry):
                task_ids.append((str(entry["task_id"]), str(entry["project_id"])))
                continue
            raise ValueError(
                f"Invalid entry at index {index}. Expected [task_id, project_id] "
                "or {'task_id': ..., 'project_id': ...}."
            )

        if args.tasks_command == "batch-delete":
            response = await client.delete_tasks(task_ids)
            action = "batch-delete"
        else:
            response = await client.complete_tasks(task_ids)
            action = "batch-done"

        if json_output:
            _print_json({
                "success": True,
                "action": action,
                "result": response,
            })
        else:
            _print_batch_result_pretty(action, response)
        return 0

    if args.tasks_command == "batch-move":
        moves = _load_json_array_from_file(args.file)
        response = await client.move_tasks(moves)
        if json_output:
            _print_json({
                "success": True,
                "action": "batch-move",
                "result": response,
            })
        else:
            _print_batch_result_pretty("batch-move", response)
        return 0

    if args.tasks_command == "batch-parent":
        assignments = _load_json_array_from_file(args.file)
        response = await client.set_task_parents(assignments)
        if json_output:
            _print_json({
                "success": True,
                "action": "batch-parent",
                "result": response,
            })
        else:
            _print_batch_result_pretty("batch-parent", response)
        return 0

    if args.tasks_command == "batch-unparent":
        assignments = _load_json_array_from_file(args.file)
        response = await client.unparent_tasks(assignments)
        if json_output:
            _print_json({
                "success": True,
                "action": "batch-unparent",
                "result": response,
            })
        else:
            _print_batch_result_pretty("batch-unparent", response)
        return 0

    if args.tasks_command == "batch-pin":
        operations = _load_json_array_from_file(args.file)
        tasks = await client.pin_tasks(operations)
        tasks_sorted = sorted(tasks, key=lambda task: _task_sort_key(task, tz))
        if json_output:
            _print_json({
                "success": True,
                "action": "batch-pin",
                "count": len(tasks_sorted),
                "tasks": [_task_to_json(task, tz) for task in tasks_sorted],
            })
        else:
            _print_task_list_pretty(
                tasks_sorted,
                None,
                None,
                tz_display_name,
                tz,
                title="Batch pin/unpin results",
                show_project=True,
            )
        return 0

    raise ValueError(f"Unknown tasks subcommand: {args.tasks_command}")


async def _run_projects_command(client: Any, args: argparse.Namespace) -> int:
    tz, configured_tz_name = _get_cli_timezone()
    tz_display_name = configured_tz_name or "local"
    json_output = bool(getattr(args, "json", False))
    current_project_id = await _resolve_project_id(client, None)

    if args.projects_command == "list":
        projects = await client.get_all_projects()
        projects_sorted = sorted(projects, key=lambda project: str(project.name).casefold())

        if json_output:
            _print_json({
                "count": len(projects_sorted),
                "current_project_id": current_project_id,
                "projects": [
                    _project_to_json(project, current_project_id)
                    for project in projects_sorted
                ],
            })
        else:
            _print_projects_pretty(projects_sorted, current_project_id)
        return 0

    if args.projects_command == "get":
        project = await client.get_project(args.project_id)
        if json_output:
            _print_json({
                "success": True,
                "project": _project_to_json(project, current_project_id),
            })
        else:
            _print_project_details_pretty(project, current_project_id)
        return 0

    if args.projects_command == "data":
        project_data = await client.get_project_tasks(args.project_id)
        if json_output:
            _print_json({
                "success": True,
                "timezone": tz_display_name,
                "data": _project_data_to_json(project_data, current_project_id, tz),
            })
        else:
            _print_project_data_pretty(project_data, current_project_id, tz, tz_display_name)
        return 0

    if args.projects_command == "create":
        project = await client.create_project(
            name=args.name,
            color=args.color,
            kind=args.kind.upper() if isinstance(args.kind, str) else args.kind,
            view_mode=args.view_mode,
            folder_id=args.folder_id,
        )
        if json_output:
            _print_json({
                "success": True,
                "project": _project_to_json(project, current_project_id),
            })
        else:
            print(f"Project created: {getattr(project, 'id', '')}")
            _print_project_details_pretty(project, current_project_id)
        return 0

    if args.projects_command == "update":
        if args.folder_id and args.remove_folder:
            raise ValueError("Use either --folder or --remove-folder, not both.")
        folder_id = "NONE" if args.remove_folder else args.folder_id
        if args.name is None and args.color is None and folder_id is None:
            raise ValueError("No update fields provided.")

        project = await client.update_project(
            project_id=args.project_id,
            name=args.name,
            color=args.color,
            folder_id=folder_id,
        )
        if json_output:
            _print_json({
                "success": True,
                "project": _project_to_json(project, current_project_id),
            })
        else:
            print(f"Project {args.project_id} updated.")
            _print_project_details_pretty(project, current_project_id)
        return 0

    if args.projects_command == "delete":
        await client.delete_project(args.project_id)
        if json_output:
            _print_json({
                "success": True,
                "action": "delete",
                "project_id": args.project_id,
            })
        else:
            print(f"Project {args.project_id} deleted.")
        return 0

    raise ValueError(f"Unknown projects subcommand: {args.projects_command}")


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

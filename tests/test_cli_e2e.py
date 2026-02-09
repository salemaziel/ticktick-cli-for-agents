"""Live end-to-end tests for CLI command surface.

These tests call the real CLI in subprocesses and validate JSON output
against reference schemas stored under tests/e2e/references.

Run intentionally:

    TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/test_cli_e2e.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv
from jsonschema import Draft202012Validator

from ticktick_cli.parser import create_parser

ROOT_DIR = Path(__file__).resolve().parents[1]
REF_DIR = ROOT_DIR / "tests" / "e2e" / "references"

REQUIRED_ENV_VARS = [
    "TICKTICK_CLIENT_ID",
    "TICKTICK_CLIENT_SECRET",
    "TICKTICK_ACCESS_TOKEN",
    "TICKTICK_USERNAME",
    "TICKTICK_PASSWORD",
]


@dataclass
class LiveState:
    """Tracks created resources for best-effort cleanup."""

    prefix: str
    folder_ids: set[str] = field(default_factory=set)
    project_ids: set[str] = field(default_factory=set)
    tag_names: set[str] = field(default_factory=set)
    habit_ids: set[str] = field(default_factory=set)
    task_locations: dict[str, str] = field(default_factory=dict)



def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def _expected_command_keys(manifest: dict[str, Any]) -> set[str]:
    expected: set[str] = set(manifest["single_commands"])
    for group, subcommands in manifest["group_commands"].items():
        expected.update({f"{group} {subcommand}" for subcommand in subcommands})
    return expected



def _parser_command_surface() -> tuple[set[str], dict[str, set[str]]]:
    parser = create_parser()
    subparsers_action = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    single: set[str] = set()
    grouped: dict[str, set[str]] = {}

    for command, command_parser in subparsers_action.choices.items():
        nested_action = next(
            (
                action
                for action in command_parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if nested_action is None:
            single.add(command)
        else:
            grouped[command] = set(nested_action.choices.keys())

    return single, grouped



def _validate_schema(schema_catalog: dict[str, Any], schema_name: str, payload: Any) -> None:
    schema = {
        "$ref": f"#/$defs/{schema_name}",
        "$defs": schema_catalog["$defs"],
    }
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        rendered = "\n".join(
            f"- {'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        pytest.fail(f"Schema validation failed for '{schema_name}':\n{rendered}")



def _run_cli(
    args: list[str],
    *,
    json_output: bool = True,
    expected_exit_code: int = 0,
) -> Any:
    cmd = [sys.executable, "-m", "ticktick_cli", *args]
    if json_output and "--json" not in args:
        cmd.append("--json")

    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH")
    src_path = str(ROOT_DIR / "src")
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{pythonpath}" if pythonpath else src_path

    completed = subprocess.run(
        cmd,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        env=env,
    )

    if completed.returncode != expected_exit_code:
        pytest.fail(
            "CLI command failed\n"
            f"Command: {' '.join(cmd)}\n"
            f"Exit code: {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}"
        )

    if not json_output:
        return completed.stdout

    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            "Expected JSON output but parsing failed\n"
            f"Command: {' '.join(cmd)}\n"
            f"STDOUT:\n{completed.stdout}\n"
            f"STDERR:\n{completed.stderr}\n"
            f"Error: {exc}"
        )


async def _cleanup_live_state(state: LiveState) -> None:
    """Best-effort cleanup to keep test account tidy."""
    if not any([
        state.folder_ids,
        state.project_ids,
        state.tag_names,
        state.habit_ids,
        state.task_locations,
    ]):
        return

    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=True)

    from ticktick_cli.commands import _apply_v2_auth_rate_limit_workaround
    from ticktick_sdk.client import TickTickClient

    _apply_v2_auth_rate_limit_workaround()

    try:
        async with TickTickClient.from_settings() as client:
            for habit_id in list(state.habit_ids):
                try:
                    await client.delete_habit(habit_id)
                except Exception:
                    pass

            for task_id, project_id in list(state.task_locations.items()):
                try:
                    await client.delete_task(task_id, project_id)
                except Exception:
                    pass

            for project_id in list(state.project_ids):
                try:
                    await client.delete_project(project_id)
                except Exception:
                    pass

            for folder_id in list(state.folder_ids):
                try:
                    await client.delete_folder(folder_id)
                except Exception:
                    pass

            for tag_name in list(state.tag_names):
                try:
                    await client.delete_tag(tag_name)
                except Exception:
                    pass
    except Exception:
        # If client auth/config fails during teardown, do not mask test results.
        pass


@pytest.fixture(scope="module")
def e2e_enabled() -> None:
    load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)

    if os.getenv("TICKTICK_RUN_E2E") != "1":
        pytest.skip("Set TICKTICK_RUN_E2E=1 to run live CLI E2E tests.")

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing required env vars for E2E tests: {', '.join(missing)}")


@pytest.fixture
def live_state(e2e_enabled: None) -> LiveState:
    prefix = f"cli-e2e-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(4)}"
    state = LiveState(prefix=prefix)
    yield state
    asyncio.run(_cleanup_live_state(state))


def test_e2e_manifest_matches_parser_surface() -> None:
    manifest = _read_json(REF_DIR / "command_surface.json")

    expected_single = set(manifest["single_commands"])
    expected_grouped = {
        group: set(subcommands)
        for group, subcommands in manifest["group_commands"].items()
    }

    actual_single, actual_grouped = _parser_command_surface()

    assert actual_single == expected_single
    assert actual_grouped == expected_grouped


@pytest.mark.e2e
def test_cli_end_to_end_json_surface(live_state: LiveState, tmp_path: Path) -> None:
    manifest = _read_json(REF_DIR / "command_surface.json")
    schema_catalog = _read_json(REF_DIR / "output_schemas.json")
    expected_keys = _expected_command_keys(manifest)
    command_schemas: dict[str, str] = schema_catalog["command_schemas"]

    seen: set[str] = set()

    def run_json(command_key: str, args: list[str]) -> Any:
        payload = _run_cli(args, json_output=True)
        seen.add(command_key)

        schema_name = command_schemas.get(command_key)
        if schema_name:
            _validate_schema(schema_catalog, schema_name, payload)

        return payload

    def run_text_help(command_key: str, args: list[str]) -> str:
        output = _run_cli(args, json_output=False)
        seen.add(command_key)
        assert "usage:" in output.lower()
        return output

    def write_json_file(filename: str, payload: Any) -> str:
        path = tmp_path / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    def track_task(task_payload: dict[str, Any]) -> None:
        task_id = task_payload.get("id")
        project_id = task_payload.get("project_id")
        if isinstance(task_id, str) and isinstance(project_id, str):
            live_state.task_locations[task_id] = project_id

    run_text_help("server", ["server", "--help"])
    run_text_help("auth", ["auth", "--help"])

    sync_payload = run_json("sync", ["sync"])
    assert isinstance(sync_payload["sync"], dict)

    run_json("user profile", ["user", "profile"])
    run_json("user status", ["user", "status"])
    run_json("user statistics", ["user", "statistics"])
    run_json("user preferences", ["user", "preferences"])

    run_json("focus heatmap", ["focus", "heatmap", "--days", "7"])
    run_json("focus by-tag", ["focus", "by-tag", "--days", "7"])

    run_json("tags list", ["tags", "list"])

    folder_name = f"{live_state.prefix}-folder"
    folder_payload = run_json("folders create", ["folders", "create", folder_name])
    folder_id = folder_payload["folder"]["id"]
    assert isinstance(folder_id, str)
    live_state.folder_ids.add(folder_id)

    renamed_folder_name = f"{folder_name}-renamed"
    run_json("folders rename", ["folders", "rename", folder_id, renamed_folder_name])
    run_json("folders list", ["folders", "list"])

    project_name = f"{live_state.prefix}-project"
    project_payload = run_json(
        "projects create",
        ["projects", "create", project_name, "--view", "list", "--folder", folder_id],
    )
    project_id = project_payload["project"]["id"]
    assert isinstance(project_id, str)
    live_state.project_ids.add(project_id)

    run_json("projects get", ["projects", "get", project_id])
    run_json("projects data", ["projects", "data", project_id])
    run_json(
        "projects update",
        [
            "projects",
            "update",
            project_id,
            "--name",
            f"{project_name}-updated",
            "--color",
            "#57A8FF",
        ],
    )
    run_json("projects list", ["projects", "list"])

    kanban_project_payload = run_json(
        "projects create",
        ["projects", "create", f"{live_state.prefix}-kanban", "--view", "kanban", "--folder", folder_id],
    )
    kanban_project_id = kanban_project_payload["project"]["id"]
    assert isinstance(kanban_project_id, str)
    live_state.project_ids.add(kanban_project_id)

    column_payload = run_json(
        "columns create",
        ["columns", "create", "--project", kanban_project_id, f"{live_state.prefix}-column"],
    )
    column_id = column_payload["column"]["id"]
    assert isinstance(column_id, str)

    run_json("columns update", [
        "columns",
        "update",
        column_id,
        "--project",
        kanban_project_id,
        "--name",
        f"{live_state.prefix}-column-updated",
        "--sort",
        "1",
    ])
    run_json("columns list", ["columns", "list", "--project", kanban_project_id])

    lookup_tag = f"{live_state.prefix}-lookup-tag"
    run_json("tags create", ["tags", "create", lookup_tag, "--color", "#F18181"])
    live_state.tag_names.add(lookup_tag)

    run_json("tags update", ["tags", "update", lookup_tag, "--color", "#57A8FF"])

    today = date.today()
    yesterday = today - timedelta(days=1)

    main_task_payload = run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-main-task",
            "--project",
            project_id,
            "--content",
            "main note",
            "--description",
            "main checklist desc",
            "--priority",
            "high",
            "--tags",
            lookup_tag,
        ],
    )
    main_task = main_task_payload["task"]
    main_task_id = main_task["id"]
    track_task(main_task)

    quick_task_payload = run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-quick-task", "--project", project_id],
    )
    quick_task = quick_task_payload["task"]
    quick_task_id = quick_task["id"]
    track_task(quick_task)

    run_json("tasks get", ["tasks", "get", main_task_id, "--project", project_id])

    updated_title = f"{live_state.prefix}-main-task-updated"
    updated_payload = run_json(
        "tasks update",
        [
            "tasks",
            "update",
            main_task_id,
            "--project",
            project_id,
            "--title",
            updated_title,
            "--content",
            "updated note",
            "--priority",
            "high",
            "--tags",
            lookup_tag,
        ],
    )
    track_task(updated_payload["task"])

    run_json("tasks list", ["tasks", "list", "--project", project_id])

    search_payload = run_json("tasks search", ["tasks", "search", live_state.prefix, "--project", project_id])
    assert any(task.get("id") == main_task_id for task in search_payload.get("tasks", []))

    by_tag_payload = run_json("tasks by-tag", ["tasks", "by-tag", lookup_tag, "--project", project_id])
    assert any(task.get("id") == main_task_id for task in by_tag_payload.get("tasks", []))

    run_json("tasks by-priority", ["tasks", "by-priority", "high", "--project", project_id])

    today_task_payload = run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-today-task",
            "--project",
            project_id,
            "--due",
            today.isoformat(),
        ],
    )
    today_task_id = today_task_payload["task"]["id"]
    track_task(today_task_payload["task"])

    overdue_task_payload = run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-overdue-task",
            "--project",
            project_id,
            "--due",
            yesterday.isoformat(),
        ],
    )
    overdue_task_id = overdue_task_payload["task"]["id"]
    track_task(overdue_task_payload["task"])

    run_json("tasks today", ["tasks", "today", "--project", project_id])
    run_json("tasks overdue", ["tasks", "overdue", "--project", project_id])

    parent_task_payload = run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-parent", "--project", project_id],
    )
    parent_task_id = parent_task_payload["task"]["id"]
    track_task(parent_task_payload["task"])

    child_task_payload = run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-child", "--project", project_id],
    )
    child_task_id = child_task_payload["task"]["id"]
    track_task(child_task_payload["task"])

    run_json("tasks subtask", [
        "tasks",
        "subtask",
        child_task_id,
        "--project",
        project_id,
        "--parent",
        parent_task_id,
    ])

    run_json("tasks unparent", ["tasks", "unparent", child_task_id, "--project", project_id])

    run_json("tasks pin", ["tasks", "pin", main_task_id, "--project", project_id])
    run_json("tasks unpin", ["tasks", "unpin", main_task_id, "--project", project_id])

    run_json("tasks move", [
        "tasks",
        "move",
        quick_task_id,
        "--from-project",
        project_id,
        "--to-project",
        kanban_project_id,
    ])
    live_state.task_locations[quick_task_id] = kanban_project_id

    column_task_payload = run_json("tasks column", [
        "tasks",
        "column",
        quick_task_id,
        "--project",
        kanban_project_id,
        "--column",
        column_id,
    ])
    track_task(column_task_payload["task"])

    clear_column_payload = run_json("tasks column", [
        "tasks",
        "column",
        quick_task_id,
        "--project",
        kanban_project_id,
        "--clear-column",
    ])
    track_task(clear_column_payload["task"])

    run_json("tasks done", ["tasks", "done", today_task_id, "--project", project_id])
    run_json("tasks abandon", ["tasks", "abandon", overdue_task_id, "--project", project_id])

    run_json("tasks completed", ["tasks", "completed", "--days", "30", "--project", project_id])
    run_json("tasks abandoned", ["tasks", "abandoned", "--days", "30", "--project", project_id])

    run_json("tasks delete", ["tasks", "delete", child_task_id, "--project", project_id])
    live_state.task_locations.pop(child_task_id, None)

    run_json("tasks deleted", ["tasks", "deleted", "--project", project_id])

    batch_create_specs = [
        {
            "title": f"{live_state.prefix}-batch-1",
            "project_id": project_id,
            "priority": "medium"
        },
        {
            "title": f"{live_state.prefix}-batch-2",
            "project_id": project_id,
            "priority": "low"
        },
        {
            "title": f"{live_state.prefix}-batch-3",
            "project_id": project_id,
            "priority": "none"
        }
    ]
    batch_create_file = write_json_file("batch-create.json", batch_create_specs)
    batch_create_payload = run_json("tasks batch-create", ["tasks", "batch-create", "--file", batch_create_file])

    batch_tasks = batch_create_payload["tasks"]
    batch_ids = [task["id"] for task in batch_tasks]
    for task in batch_tasks:
        track_task(task)

    batch_update_specs = [
        {
            "task_id": batch_ids[0],
            "project_id": project_id,
            "title": f"{live_state.prefix}-batch-1-updated",
            "priority": 5
        },
        {
            "task_id": batch_ids[1],
            "project_id": project_id,
            "content": "batch updated content"
        }
    ]
    batch_update_file = write_json_file("batch-update.json", batch_update_specs)
    run_json("tasks batch-update", ["tasks", "batch-update", "--file", batch_update_file])

    batch_parent_specs = [
        {"task_id": batch_ids[1], "project_id": project_id, "parent_id": batch_ids[0]},
        {"task_id": batch_ids[2], "project_id": project_id, "parent_id": batch_ids[0]}
    ]
    batch_parent_file = write_json_file("batch-parent.json", batch_parent_specs)
    run_json("tasks batch-parent", ["tasks", "batch-parent", "--file", batch_parent_file])

    batch_unparent_specs = [{"task_id": batch_ids[2], "project_id": project_id}]
    batch_unparent_file = write_json_file("batch-unparent.json", batch_unparent_specs)
    run_json("tasks batch-unparent", ["tasks", "batch-unparent", "--file", batch_unparent_file])

    batch_pin_specs = [
        {"task_id": batch_ids[0], "project_id": project_id, "pin": True},
        {"task_id": batch_ids[1], "project_id": project_id, "pin": False}
    ]
    batch_pin_file = write_json_file("batch-pin.json", batch_pin_specs)
    run_json("tasks batch-pin", ["tasks", "batch-pin", "--file", batch_pin_file])

    batch_done_specs = [[batch_ids[1], project_id]]
    batch_done_file = write_json_file("batch-done.json", batch_done_specs)
    run_json("tasks batch-done", ["tasks", "batch-done", "--file", batch_done_file])

    batch_move_specs = [
        {
            "task_id": batch_ids[2],
            "from_project_id": project_id,
            "to_project_id": kanban_project_id
        }
    ]
    batch_move_file = write_json_file("batch-move.json", batch_move_specs)
    run_json("tasks batch-move", ["tasks", "batch-move", "--file", batch_move_file])
    live_state.task_locations[batch_ids[2]] = kanban_project_id

    batch_delete_specs = [
        [batch_ids[0], project_id],
        [batch_ids[1], project_id],
        [batch_ids[2], kanban_project_id]
    ]
    batch_delete_file = write_json_file("batch-delete.json", batch_delete_specs)
    run_json("tasks batch-delete", ["tasks", "batch-delete", "--file", batch_delete_file])

    for batch_id in batch_ids:
        live_state.task_locations.pop(batch_id, None)

    merge_source_tag = f"{live_state.prefix}-merge-source"
    merge_target_tag = f"{live_state.prefix}-merge-target"

    run_json("tags create", ["tags", "create", merge_source_tag])
    live_state.tag_names.add(merge_source_tag)
    run_json("tags create", ["tags", "create", merge_target_tag])
    live_state.tag_names.add(merge_target_tag)

    run_json("tags rename", ["tags", "rename", merge_source_tag, f"{merge_source_tag}-renamed"])
    live_state.tag_names.discard(merge_source_tag)
    renamed_merge_source_tag = f"{merge_source_tag}-renamed"
    live_state.tag_names.add(renamed_merge_source_tag)

    run_json("tags merge", ["tags", "merge", renamed_merge_source_tag, merge_target_tag])
    live_state.tag_names.discard(renamed_merge_source_tag)

    run_json("tags delete", ["tags", "delete", merge_target_tag])
    live_state.tag_names.discard(merge_target_tag)

    habit_name = f"{live_state.prefix}-habit"
    habit_payload = run_json("habits create", [
        "habits",
        "create",
        habit_name,
        "--goal",
        "1.0",
        "--unit",
        "Count",
    ])
    habit_id = habit_payload["habit"]["id"]
    live_state.habit_ids.add(habit_id)

    run_json("habits list", ["habits", "list"])
    run_json("habits get", ["habits", "get", habit_id])
    run_json("habits sections", ["habits", "sections"])
    run_json("habits preferences", ["habits", "preferences"])

    run_json("habits update", [
        "habits",
        "update",
        habit_id,
        "--name",
        f"{habit_name}-updated",
        "--target-days",
        "3",
        "--encouragement",
        "keep going",
    ])

    run_json("habits checkin", ["habits", "checkin", habit_id, "--value", "1.0", "--date", today.isoformat()])

    habit_batch_checkins = [
        {
            "habit_id": habit_id,
            "value": 1.0,
            "checkin_date": yesterday.isoformat()
        }
    ]
    habit_batch_file = write_json_file("habit-batch-checkin.json", habit_batch_checkins)
    run_json("habits batch-checkin", ["habits", "batch-checkin", "--file", habit_batch_file])

    run_json("habits checkins", ["habits", "checkins", habit_id, "--after-stamp", "0"])

    run_json("habits archive", ["habits", "archive", habit_id])
    run_json("habits unarchive", ["habits", "unarchive", habit_id])

    run_json("habits delete", ["habits", "delete", habit_id])
    live_state.habit_ids.discard(habit_id)

    run_json("columns delete", ["columns", "delete", column_id, "--project", kanban_project_id])

    run_json("projects delete", ["projects", "delete", kanban_project_id])
    live_state.project_ids.discard(kanban_project_id)

    run_json("projects delete", ["projects", "delete", project_id])
    live_state.project_ids.discard(project_id)

    run_json("folders delete", ["folders", "delete", folder_id])
    live_state.folder_ids.discard(folder_id)

    run_json("tags delete", ["tags", "delete", lookup_tag])
    live_state.tag_names.discard(lookup_tag)

    assert seen == expected_keys

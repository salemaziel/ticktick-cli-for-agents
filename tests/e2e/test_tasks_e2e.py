"""Live E2E tests for task command area with semantic content checks."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import pytest



def _track_task(live_state, task_payload: dict[str, Any]) -> None:
    task_id = task_payload.get("id")
    project_id = task_payload.get("project_id")
    if isinstance(task_id, str) and isinstance(project_id, str):
        live_state.task_locations[task_id] = project_id



def _create_workspace(cli, live_state) -> dict[str, str]:
    project_payload = cli.run_json(
        "projects create",
        ["projects", "create", f"{live_state.prefix}-Daily Planner", "--view", "list"],
    )
    project_id = project_payload["project"]["id"]
    live_state.project_ids.add(project_id)

    kanban_payload = cli.run_json(
        "projects create",
        ["projects", "create", f"{live_state.prefix}-Workflow", "--view", "kanban"],
    )
    kanban_project_id = kanban_payload["project"]["id"]
    live_state.project_ids.add(kanban_project_id)

    column_payload = cli.run_json(
        "columns create",
        ["columns", "create", "--project", kanban_project_id, f"{live_state.prefix}-Doing", "--sort", "1"],
    )
    column_id = column_payload["column"]["id"]

    tag_name = f"{live_state.prefix}-home"
    tag_payload = cli.run_json("tags create", ["tags", "create", tag_name, "--color", "#57A8FF"])
    assert tag_payload["tag"]["name"] == tag_name
    live_state.tag_names.add(tag_name)

    return {
        "project_id": project_id,
        "kanban_project_id": kanban_project_id,
        "column_id": column_id,
        "tag_name": tag_name,
    }


@pytest.mark.e2e
@pytest.mark.e2e_tasks
def test_tasks_lifecycle_semantic_content(cli, live_state, eventually) -> None:
    workspace = _create_workspace(cli, live_state)

    today = date.today()
    yesterday = today - timedelta(days=1)

    main_create = cli.run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-Prepare grocery list",
            "--project",
            workspace["project_id"],
            "--content",
            "milk, eggs, vegetables",
            "--description",
            "check pantry first",
            "--priority",
            "high",
            "--tags",
            workspace["tag_name"],
            "--due",
            today.isoformat(),
        ],
    )
    main_task = main_create["task"]
    main_task_id = main_task["id"]
    _track_task(live_state, main_task)

    assert main_task["title"] == f"{live_state.prefix}-Prepare grocery list"
    assert main_task["content"] == "milk, eggs, vegetables"
    assert main_task["description"] == "check pantry first"
    assert main_task["priority"] == 5
    assert workspace["tag_name"] in main_task["tags"]

    main_get = cli.run_json("tasks get", ["tasks", "get", main_task_id, "--project", workspace["project_id"]])
    assert main_get["task"]["id"] == main_task_id
    assert main_get["task"]["title"] == main_task["title"]
    assert main_get["task"]["content"] == main_task["content"]

    updated_title = f"{live_state.prefix}-Prepare weekly grocery list"
    main_update = cli.run_json(
        "tasks update",
        [
            "tasks",
            "update",
            main_task_id,
            "--project",
            workspace["project_id"],
            "--title",
            updated_title,
            "--content",
            "milk, eggs, vegetables, pasta",
            "--priority",
            "low",
            "--tags",
            workspace["tag_name"],
        ],
    )
    assert main_update["task"]["title"] == updated_title
    assert main_update["task"]["content"] == "milk, eggs, vegetables, pasta"
    assert main_update["task"]["priority"] == 1

    quick_create = cli.run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-Book dentist", "--project", workspace["project_id"]],
    )
    quick_task = quick_create["task"]
    quick_task_id = quick_task["id"]
    _track_task(live_state, quick_task)
    assert quick_task["title"] == f"{live_state.prefix}-Book dentist"

    search_payload = cli.run_json(
        "tasks search",
        ["tasks", "search", "weekly grocery", "--project", workspace["project_id"]],
    )
    assert any(task["id"] == main_task_id for task in search_payload["tasks"])

    by_tag_payload = cli.run_json(
        "tasks by-tag",
        ["tasks", "by-tag", workspace["tag_name"], "--project", workspace["project_id"]],
    )
    assert any(task["id"] == main_task_id for task in by_tag_payload["tasks"])

    by_priority_payload = cli.run_json(
        "tasks by-priority",
        ["tasks", "by-priority", "low", "--project", workspace["project_id"]],
    )
    assert any(task["id"] == main_task_id for task in by_priority_payload["tasks"])

    move_payload = cli.run_json(
        "tasks move",
        [
            "tasks",
            "move",
            quick_task_id,
            "--from-project",
            workspace["project_id"],
            "--to-project",
            workspace["kanban_project_id"],
        ],
    )
    assert move_payload["to_project_id"] == workspace["kanban_project_id"]
    live_state.task_locations[quick_task_id] = workspace["kanban_project_id"]

    column_set = cli.run_json(
        "tasks column",
        [
            "tasks",
            "column",
            quick_task_id,
            "--project",
            workspace["kanban_project_id"],
            "--column",
            workspace["column_id"],
        ],
    )
    assert column_set["task"]["column_id"] == workspace["column_id"]

    column_clear = cli.run_json(
        "tasks column",
        [
            "tasks",
            "column",
            quick_task_id,
            "--project",
            workspace["kanban_project_id"],
            "--clear-column",
        ],
    )
    assert column_clear["task"]["column_id"] is None

    parent_task = cli.run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-Plan weekend", "--project", workspace["project_id"]],
    )["task"]
    parent_task_id = parent_task["id"]
    _track_task(live_state, parent_task)

    child_task = cli.run_json(
        "tasks quick-add",
        ["tasks", "quick-add", f"{live_state.prefix}-Buy train tickets", "--project", workspace["project_id"]],
    )["task"]
    child_task_id = child_task["id"]
    _track_task(live_state, child_task)

    cli.run_json(
        "tasks subtask",
        [
            "tasks",
            "subtask",
            child_task_id,
            "--project",
            workspace["project_id"],
            "--parent",
            parent_task_id,
        ],
    )

    child_after_subtask = cli.run_json(
        "tasks get",
        ["tasks", "get", child_task_id, "--project", workspace["project_id"]],
    )
    assert child_after_subtask["task"]["parent_id"] == parent_task_id

    cli.run_json("tasks unparent", ["tasks", "unparent", child_task_id, "--project", workspace["project_id"]])

    child_after_unparent = cli.run_json(
        "tasks get",
        ["tasks", "get", child_task_id, "--project", workspace["project_id"]],
    )
    assert child_after_unparent["task"]["parent_id"] is None

    today_task = cli.run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-Today standup prep",
            "--project",
            workspace["project_id"],
            "--due",
            today.isoformat(),
        ],
    )["task"]
    today_task_id = today_task["id"]
    _track_task(live_state, today_task)

    overdue_task = cli.run_json(
        "tasks add",
        [
            "tasks",
            "add",
            f"{live_state.prefix}-Pay utility bill",
            "--project",
            workspace["project_id"],
            "--due",
            yesterday.isoformat(),
        ],
    )["task"]
    overdue_task_id = overdue_task["id"]
    _track_task(live_state, overdue_task)

    def _today_visible() -> None:
        payload = cli.run_json("tasks today", ["tasks", "today", "--project", workspace["project_id"]])
        assert today_task_id in {task["id"] for task in payload["tasks"]}

    eventually(_today_visible, timeout=20.0, interval=1.0)

    def _overdue_visible() -> None:
        payload = cli.run_json("tasks overdue", ["tasks", "overdue", "--project", workspace["project_id"]])
        assert overdue_task_id in {task["id"] for task in payload["tasks"]}

    eventually(_overdue_visible, timeout=20.0, interval=1.0)

    pin_payload = cli.run_json("tasks pin", ["tasks", "pin", main_task_id, "--project", workspace["project_id"]])
    assert pin_payload["task"]["pinned_time"] is not None

    unpin_payload = cli.run_json("tasks unpin", ["tasks", "unpin", main_task_id, "--project", workspace["project_id"]])
    assert unpin_payload["task"]["pinned_time"] is None

    done_payload = cli.run_json("tasks done", ["tasks", "done", today_task_id, "--project", workspace["project_id"]])
    assert done_payload["task_id"] == today_task_id

    abandon_payload = cli.run_json(
        "tasks abandon",
        ["tasks", "abandon", overdue_task_id, "--project", workspace["project_id"]],
    )
    assert abandon_payload["task_id"] == overdue_task_id

    def _completed_visible() -> None:
        payload = cli.run_json(
            "tasks completed",
            ["tasks", "completed", "--days", "30", "--project", workspace["project_id"]],
        )
        assert today_task_id in {task["id"] for task in payload["tasks"]}

    eventually(_completed_visible, timeout=30.0, interval=1.0)

    def _abandoned_visible() -> None:
        payload = cli.run_json(
            "tasks abandoned",
            ["tasks", "abandoned", "--days", "30", "--project", workspace["project_id"]],
        )
        assert overdue_task_id in {task["id"] for task in payload["tasks"]}

    eventually(_abandoned_visible, timeout=30.0, interval=1.0)

    cli.run_json("tasks delete", ["tasks", "delete", child_task_id, "--project", workspace["project_id"]])
    live_state.task_locations.pop(child_task_id, None)

    cli.run_json("tasks deleted", ["tasks", "deleted", "--project", workspace["project_id"]])


@pytest.mark.e2e
@pytest.mark.e2e_tasks
def test_tasks_batch_operations_semantic_content(cli, live_state, write_json_file, eventually) -> None:
    workspace = _create_workspace(cli, live_state)

    prefix = f"{live_state.prefix}-batch"
    create_specs = [
        {
            "title": f"{prefix}-Weekly meal prep",
            "project_id": workspace["project_id"],
            "priority": "medium",
        },
        {
            "title": f"{prefix}-Car maintenance",
            "project_id": workspace["project_id"],
            "priority": "low",
        },
        {
            "title": f"{prefix}-Read project brief",
            "project_id": workspace["project_id"],
            "priority": "none",
        },
    ]
    create_file = write_json_file("tasks-batch-create.json", create_specs)
    batch_create = cli.run_json("tasks batch-create", ["tasks", "batch-create", "--file", create_file])

    assert batch_create["count"] == 3
    created_tasks = batch_create["tasks"]
    created_titles = {task["title"] for task in created_tasks}
    assert created_titles == {spec["title"] for spec in create_specs}

    task_ids = [task["id"] for task in created_tasks]
    for task in created_tasks:
        _track_task(live_state, task)

    update_specs = [
        {
            "task_id": task_ids[0],
            "project_id": workspace["project_id"],
            "title": f"{prefix}-Weekly meal prep (updated)",
            "content": "buy vegetables and protein",
            "priority": 5,
        },
        {
            "task_id": task_ids[1],
            "project_id": workspace["project_id"],
            "content": "book service appointment",
        },
    ]
    update_file = write_json_file("tasks-batch-update.json", update_specs)
    cli.run_json("tasks batch-update", ["tasks", "batch-update", "--file", update_file])

    updated_task = cli.run_json(
        "tasks get",
        ["tasks", "get", task_ids[0], "--project", workspace["project_id"]],
    )["task"]
    assert updated_task["title"] == f"{prefix}-Weekly meal prep (updated)"
    assert updated_task["content"] == "buy vegetables and protein"
    assert updated_task["priority"] == 5

    parent_file = write_json_file(
        "tasks-batch-parent.json",
        [{"task_id": task_ids[1], "project_id": workspace["project_id"], "parent_id": task_ids[0]}],
    )
    cli.run_json("tasks batch-parent", ["tasks", "batch-parent", "--file", parent_file])

    def _parent_applied() -> None:
        payload = cli.run_json(
            "tasks get",
            ["tasks", "get", task_ids[1], "--project", workspace["project_id"]],
        )
        assert payload["task"]["parent_id"] == task_ids[0]

    eventually(_parent_applied, timeout=20.0, interval=1.0)

    unparent_file = write_json_file(
        "tasks-batch-unparent.json",
        [{"task_id": task_ids[1], "project_id": workspace["project_id"]}],
    )
    cli.run_json("tasks batch-unparent", ["tasks", "batch-unparent", "--file", unparent_file])

    def _unparent_applied() -> None:
        payload = cli.run_json(
            "tasks get",
            ["tasks", "get", task_ids[1], "--project", workspace["project_id"]],
        )
        assert payload["task"]["parent_id"] is None

    eventually(_unparent_applied, timeout=20.0, interval=1.0)

    pin_file = write_json_file(
        "tasks-batch-pin.json",
        [
            {"task_id": task_ids[0], "project_id": workspace["project_id"], "pin": True},
            {"task_id": task_ids[1], "project_id": workspace["project_id"], "pin": False},
        ],
    )
    pin_payload = cli.run_json("tasks batch-pin", ["tasks", "batch-pin", "--file", pin_file])
    assert pin_payload["count"] == 2
    assert {task["id"] for task in pin_payload["tasks"]} == {task_ids[0], task_ids[1]}

    done_file = write_json_file(
        "tasks-batch-done.json",
        [[task_ids[1], workspace["project_id"]]],
    )
    cli.run_json("tasks batch-done", ["tasks", "batch-done", "--file", done_file])

    def _batch_done_visible() -> None:
        payload = cli.run_json(
            "tasks completed",
            ["tasks", "completed", "--days", "30", "--project", workspace["project_id"]],
        )
        assert task_ids[1] in {task["id"] for task in payload["tasks"]}

    eventually(_batch_done_visible, timeout=30.0, interval=1.0)

    move_file = write_json_file(
        "tasks-batch-move.json",
        [
            {
                "task_id": task_ids[2],
                "from_project_id": workspace["project_id"],
                "to_project_id": workspace["kanban_project_id"],
            }
        ],
    )
    cli.run_json("tasks batch-move", ["tasks", "batch-move", "--file", move_file])
    live_state.task_locations[task_ids[2]] = workspace["kanban_project_id"]

    moved_task = cli.run_json(
        "tasks get",
        ["tasks", "get", task_ids[2], "--project", workspace["kanban_project_id"]],
    )["task"]
    assert moved_task["project_id"] == workspace["kanban_project_id"]

    delete_file = write_json_file(
        "tasks-batch-delete.json",
        [
            [task_ids[0], workspace["project_id"]],
            [task_ids[1], workspace["project_id"]],
            [task_ids[2], workspace["kanban_project_id"]],
        ],
    )
    cli.run_json("tasks batch-delete", ["tasks", "batch-delete", "--file", delete_file])

    def _batch_deleted() -> None:
        project_search = cli.run_json(
            "tasks search",
            ["tasks", "search", prefix, "--project", workspace["project_id"]],
        )
        kanban_search = cli.run_json(
            "tasks search",
            ["tasks", "search", prefix, "--project", workspace["kanban_project_id"]],
        )
        assert not any(task["id"] in task_ids for task in project_search["tasks"])
        assert not any(task["id"] in task_ids for task in kanban_search["tasks"])

    eventually(_batch_deleted, timeout=30.0, interval=1.0)

    for task_id in task_ids:
        live_state.task_locations.pop(task_id, None)

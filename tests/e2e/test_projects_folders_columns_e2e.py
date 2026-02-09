"""Live E2E tests for folders, projects, and columns."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
@pytest.mark.e2e_projects
def test_projects_folders_columns_flow(cli, live_state, eventually) -> None:
    folder_name = f"{live_state.prefix}-Personal Areas"
    renamed_folder_name = f"{folder_name}-Renamed"

    folder_create = cli.run_json("folders create", ["folders", "create", folder_name])
    folder_id = folder_create["folder"]["id"]
    assert isinstance(folder_id, str)
    assert folder_create["folder"]["name"] == folder_name
    live_state.folder_ids.add(folder_id)

    folder_rename = cli.run_json("folders rename", ["folders", "rename", folder_id, renamed_folder_name])
    assert folder_rename["folder"]["id"] == folder_id
    assert folder_rename["folder"]["name"] == renamed_folder_name

    folder_list = cli.run_json("folders list", ["folders", "list"])
    folder_ids = {item["id"] for item in folder_list["folders"]}
    assert folder_id in folder_ids

    project_name = f"{live_state.prefix}-Home Planning"
    project_create = cli.run_json(
        "projects create",
        ["projects", "create", project_name, "--view", "list", "--folder", folder_id],
    )
    project_id = project_create["project"]["id"]
    assert isinstance(project_id, str)
    assert project_create["project"]["name"] == project_name
    assert project_create["project"]["folder_id"] == folder_id
    live_state.project_ids.add(project_id)

    project_get = cli.run_json("projects get", ["projects", "get", project_id])
    assert project_get["project"]["id"] == project_id
    assert project_get["project"]["name"] == project_name

    updated_name = f"{project_name} Updated"
    project_update = cli.run_json(
        "projects update",
        [
            "projects",
            "update",
            project_id,
            "--name",
            updated_name,
            "--color",
            "#57A8FF",
        ],
    )
    assert project_update["project"]["id"] == project_id
    assert project_update["project"]["name"] == updated_name
    assert project_update["project"]["color"] == "#57A8FF"

    project_data = cli.run_json("projects data", ["projects", "data", project_id])
    assert project_data["data"]["project"]["id"] == project_id
    assert isinstance(project_data["data"]["tasks"], list)
    assert isinstance(project_data["data"]["columns"], list)

    project_list = cli.run_json("projects list", ["projects", "list"])
    project_ids = {item["id"] for item in project_list["projects"]}
    assert project_id in project_ids

    kanban_name = f"{live_state.prefix}-Workflow Board"
    kanban_project = cli.run_json(
        "projects create",
        ["projects", "create", kanban_name, "--view", "kanban", "--folder", folder_id],
    )
    kanban_project_id = kanban_project["project"]["id"]
    assert isinstance(kanban_project_id, str)
    assert kanban_project["project"]["view_mode"] == "kanban"
    live_state.project_ids.add(kanban_project_id)

    column_name = f"{live_state.prefix}-In Progress"
    column_create = cli.run_json(
        "columns create",
        ["columns", "create", "--project", kanban_project_id, column_name, "--sort", "1"],
    )
    column_id = column_create["column"]["id"]
    assert isinstance(column_id, str)
    assert column_create["column"]["project_id"] == kanban_project_id
    assert column_create["column"]["name"] == column_name

    updated_column_name = f"{column_name} Updated"
    column_update = cli.run_json(
        "columns update",
        [
            "columns",
            "update",
            column_id,
            "--project",
            kanban_project_id,
            "--name",
            updated_column_name,
            "--sort",
            "2",
        ],
    )
    assert column_update["column"]["id"] == column_id
    assert column_update["column"]["name"] == updated_column_name

    column_list = cli.run_json("columns list", ["columns", "list", "--project", kanban_project_id])
    column_ids = {item["id"] for item in column_list["columns"]}
    assert column_id in column_ids

    cli.run_json("columns delete", ["columns", "delete", column_id, "--project", kanban_project_id])

    def _column_deleted() -> None:
        payload = cli.run_json("columns list", ["columns", "list", "--project", kanban_project_id])
        assert column_id not in {item["id"] for item in payload["columns"]}

    eventually(_column_deleted, timeout=20.0, interval=1.0)

    cli.run_json("projects delete", ["projects", "delete", kanban_project_id])
    live_state.project_ids.discard(kanban_project_id)

    cli.run_json("projects delete", ["projects", "delete", project_id])
    live_state.project_ids.discard(project_id)

    def _projects_deleted() -> None:
        payload = cli.run_json("projects list", ["projects", "list"])
        ids = {item["id"] for item in payload["projects"]}
        assert project_id not in ids
        assert kanban_project_id not in ids

    eventually(_projects_deleted, timeout=30.0, interval=1.0)

    cli.run_json("folders delete", ["folders", "delete", folder_id])
    live_state.folder_ids.discard(folder_id)

    def _folder_deleted() -> None:
        payload = cli.run_json("folders list", ["folders", "list"])
        assert folder_id not in {item["id"] for item in payload["folders"]}

    eventually(_folder_deleted, timeout=20.0, interval=1.0)

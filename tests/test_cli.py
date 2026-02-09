"""CLI command tests."""

from __future__ import annotations

import json
from argparse import Namespace
from datetime import UTC, datetime

import pytest

from ticktick_cli.commands import (
    _patch_v2_session_handler_for_429,
    _run_projects_command,
    _run_tasks_command,
)
from ticktick_sdk.models import Project, Task


class _Status:
    def __init__(self, inbox_id: str) -> None:
        self.inbox_id = inbox_id


class _FakeClient:
    def __init__(
        self,
        *,
        inbox_id: str = "inbox-default",
        tasks: list[Task] | None = None,
        projects: list[Project] | None = None,
    ) -> None:
        self.inbox_id = inbox_id
        self._tasks = tasks or []
        self._projects = projects or []
        self._tasks_by_id = {task.id: task for task in self._tasks}

        self.create_task_calls: list[dict] = []
        self.complete_task_calls: list[tuple[str, str]] = []
        self.abandon_task_calls: list[tuple[str, str]] = []
        self.update_task_calls: list[Task] = []

    async def get_all_tasks(self) -> list[Task]:
        return self._tasks

    async def create_task(self, **kwargs) -> Task:
        self.create_task_calls.append(kwargs)
        due_date = kwargs.get("due_date")
        task = Task(
            id="task-new",
            project_id=kwargs["project_id"],
            title=kwargs["title"],
            content=kwargs.get("content"),
            priority=5 if kwargs.get("priority") == "high" else 0,
            due_date=due_date,
            status=0,
            tags=[],
            is_all_day=kwargs.get("all_day"),
        )
        self._tasks.append(task)
        self._tasks_by_id[task.id] = task
        return task

    async def get_task(self, task_id: str, project_id: str | None = None) -> Task:
        del project_id
        return self._tasks_by_id[task_id]

    async def complete_task(self, task_id: str, project_id: str) -> None:
        self.complete_task_calls.append((task_id, project_id))

    async def abandon_task(self, task_id: str, project_id: str) -> None:
        self.abandon_task_calls.append((task_id, project_id))

    async def update_task(self, task: Task) -> Task:
        self.update_task_calls.append(task)
        self._tasks_by_id[task.id] = task
        return task

    async def get_all_projects(self) -> list[Project]:
        return self._projects

    async def get_status(self) -> _Status:
        return _Status(self.inbox_id)


@pytest.mark.asyncio
async def test_tasks_add_uses_current_project_and_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "proj-current")
    monkeypatch.setenv("TZ", "America/New_York")

    client = _FakeClient()
    args = Namespace(
        command="tasks",
        tasks_command="add",
        title="Buy groceries",
        project_id=None,
        due="2025-02-10",
        content="Milk, eggs, bread",
        priority="high",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    assert len(client.create_task_calls) == 1
    call = client.create_task_calls[0]
    assert call["project_id"] == "proj-current"
    assert call["content"] == "Milk, eggs, bread"
    assert call["all_day"] is True
    assert call["time_zone"] == "America/New_York"
    assert call["due_date"].tzinfo is not None

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["task"]["title"] == "Buy groceries"
    assert output["task"]["content"] == "Milk, eggs, bread"


@pytest.mark.asyncio
async def test_tasks_list_filters_due_with_timezone(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "proj-1")
    monkeypatch.setenv("TZ", "America/Los_Angeles")

    tasks = [
        Task(
            id="match-task",
            project_id="proj-1",
            title="Matches local day",
            due_date=datetime(2025, 2, 10, 1, 0, tzinfo=UTC),
            priority=1,
            status=0,
            tags=[],
        ),
        Task(
            id="other-day",
            project_id="proj-1",
            title="Other local day",
            due_date=datetime(2025, 2, 10, 20, 0, tzinfo=UTC),
            priority=1,
            status=0,
            tags=[],
        ),
        Task(
            id="other-project",
            project_id="proj-2",
            title="Other project",
            due_date=datetime(2025, 2, 10, 1, 0, tzinfo=UTC),
            priority=1,
            status=0,
            tags=[],
        ),
    ]

    client = _FakeClient(tasks=tasks)
    args = Namespace(
        command="tasks",
        tasks_command="list",
        project_id=None,
        due="2025-02-09",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 1
    assert output["tasks"][0]["id"] == "match-task"


@pytest.mark.asyncio
async def test_tasks_list_json_preserves_unicode_titles(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "proj-1")
    monkeypatch.setenv("TZ", "Europe/Warsaw")

    unicode_title = "\u041c\u044b\u0442\u044c\u0451 \u0433\u0430\u0440\u0430\u0436\u0430"
    tasks = [
        Task(
            id="unicode-task",
            project_id="proj-1",
            title=unicode_title,
            due_date=datetime(2026, 2, 9, 0, 0, tzinfo=UTC),
            priority=0,
            status=0,
            tags=[],
        ),
    ]

    client = _FakeClient(tasks=tasks)
    args = Namespace(
        command="tasks",
        tasks_command="list",
        project_id=None,
        due="2026-02-09",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    raw_output = capsys.readouterr().out
    assert "\\u041c" not in raw_output

    output = json.loads(raw_output)
    assert output["tasks"][0]["title"] == unicode_title


@pytest.mark.asyncio
async def test_tasks_list_json_includes_description_fields(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "proj-1")
    monkeypatch.setenv("TZ", "UTC")

    tasks = [
        Task(
            id="task-with-notes",
            project_id="proj-1",
            title="Task with notes",
            content="Detailed content",
            desc="Checklist description",
            due_date=datetime(2026, 2, 9, 12, 0, tzinfo=UTC),
            priority=0,
            status=0,
            tags=[],
        ),
    ]

    client = _FakeClient(tasks=tasks)
    args = Namespace(
        command="tasks",
        tasks_command="list",
        project_id=None,
        due="2026-02-09",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    task = output["tasks"][0]
    assert task["content"] == "Detailed content"
    assert task["description"] == "Checklist description"
    assert "notes" not in task


@pytest.mark.asyncio
async def test_tasks_done_resolves_project_from_task(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TICKTICK_CURRENT_PROJECT_ID", raising=False)
    task = Task(
        id="task-1",
        project_id="proj-from-task",
        title="Task",
        priority=0,
        status=0,
        tags=[],
    )
    client = _FakeClient(tasks=[task])

    args = Namespace(
        command="tasks",
        tasks_command="done",
        task_id="task-1",
        project_id=None,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.complete_task_calls == [("task-1", "proj-from-task")]

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "done"


@pytest.mark.asyncio
async def test_tasks_abandon_resolves_project_from_task(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TICKTICK_CURRENT_PROJECT_ID", raising=False)
    task = Task(
        id="task-2",
        project_id="proj-from-task",
        title="Task",
        priority=0,
        status=0,
        tags=[],
    )
    client = _FakeClient(tasks=[task])

    args = Namespace(
        command="tasks",
        tasks_command="abandon",
        task_id="task-2",
        project_id=None,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.abandon_task_calls == [("task-2", "proj-from-task")]

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "abandon"


@pytest.mark.asyncio
async def test_tasks_abandon_falls_back_to_update_for_older_sdk(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TICKTICK_CURRENT_PROJECT_ID", raising=False)
    task = Task(
        id="task-3",
        project_id="proj-from-task",
        title="Task",
        priority=0,
        status=0,
        tags=[],
    )
    client = _FakeClient(tasks=[task])
    client.abandon_task = None  # type: ignore[assignment]

    args = Namespace(
        command="tasks",
        tasks_command="abandon",
        task_id="task-3",
        project_id=None,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.update_task_calls
    assert client.update_task_calls[0].status == -1

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "abandon"


@pytest.mark.asyncio
async def test_projects_list_marks_current_project(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "project-a")

    projects = [
        Project(id="project-a", name="Alpha"),
        Project(id="project-b", name="Beta"),
    ]
    client = _FakeClient(projects=projects)

    args = Namespace(
        command="projects",
        projects_command="list",
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["current_project_id"] == "project-a"
    assert output["count"] == 2

    by_id = {project["id"]: project for project in output["projects"]}
    assert by_id["project-a"]["is_current"] is True
    assert by_id["project-b"]["is_current"] is False


def test_patch_v2_session_handler_for_429_patches_legacy_headers(monkeypatch) -> None:
    class LegacySessionHandler:
        DEFAULT_USER_AGENT = "legacy-agent"

        def __init__(self, device_id: str | None = None) -> None:
            self.device_id = device_id or "legacy-device"

        def _get_x_device_header(self) -> str:
            return json.dumps({
                "platform": "web",
                "version": 6430,
                "id": self.device_id,
            })

        def _get_headers(self) -> dict[str, str]:
            return {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "X-Device": self._get_x_device_header(),
            }

    monkeypatch.setenv("TICKTICK_HOST", "dida365.com")
    applied = _patch_v2_session_handler_for_429(LegacySessionHandler)
    assert applied is True

    patched = LegacySessionHandler(device_id="abc123")
    headers = patched._get_headers()
    assert headers["Origin"] == "https://dida365.com"
    assert headers["Referer"] == "https://dida365.com/"

    x_device = json.loads(headers["X-Device"])
    assert x_device["platform"] == "web"
    assert x_device["id"] == "abc123"
    assert x_device["os"] == "macOS 10.15.7"
    assert x_device["device"] == "Chrome 120.0.0.0"
    assert x_device["channel"] == "website"


def test_patch_v2_session_handler_for_429_keeps_fixed_sdk_untouched() -> None:
    class FixedSessionHandler:
        DEFAULT_USER_AGENT = "already-fixed-agent"

        def __init__(self, device_id: str | None = None) -> None:
            self.device_id = device_id or "fixed-device"

        def _get_x_device_header(self) -> str:
            return "{}"

        def _get_headers(self) -> dict[str, str]:
            return {
                "User-Agent": self.DEFAULT_USER_AGENT,
                "Origin": "https://ticktick.com",
                "Referer": "https://ticktick.com/",
                "X-Device": self._get_x_device_header(),
            }

    original_headers_method = FixedSessionHandler._get_headers
    applied = _patch_v2_session_handler_for_429(FixedSessionHandler)

    assert applied is False
    assert FixedSessionHandler._get_headers is original_headers_method

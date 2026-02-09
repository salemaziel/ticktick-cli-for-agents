"""CLI command tests."""

from __future__ import annotations

import json
from argparse import Namespace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from ticktick_cli.commands import (
    _run_columns_command,
    _run_focus_command,
    _run_folders_command,
    _run_habits_command,
    _patch_v2_session_handler_for_429,
    _run_projects_command,
    _run_tasks_command,
    _run_tags_command,
    _run_user_command,
)
from ticktick_sdk.models import Column, Project, ProjectData, ProjectGroup, Tag, Task


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
        self._projects_by_id = {project.id: project for project in self._projects}

        self.create_task_calls: list[dict] = []
        self.complete_task_calls: list[tuple[str, str]] = []
        self.abandon_task_calls: list[tuple[str, str]] = []
        self.update_task_calls: list[Task] = []
        self.delete_task_calls: list[tuple[str, str]] = []
        self.move_task_calls: list[tuple[str, str, str]] = []
        self.make_subtask_calls: list[tuple[str, str, str]] = []
        self.unparent_subtask_calls: list[tuple[str, str]] = []
        self.pin_task_calls: list[tuple[str, str]] = []
        self.unpin_task_calls: list[tuple[str, str]] = []
        self.move_task_to_column_calls: list[tuple[str, str, str | None]] = []
        self.quick_add_calls: list[tuple[str, str | None]] = []
        self.create_tasks_calls: list[list[dict]] = []
        self.update_tasks_calls: list[list[dict]] = []
        self.delete_tasks_calls: list[list[tuple[str, str]]] = []
        self.complete_tasks_calls: list[list[tuple[str, str]]] = []
        self.move_tasks_calls: list[list[dict]] = []
        self.set_task_parents_calls: list[list[dict]] = []
        self.unparent_tasks_calls: list[list[dict]] = []
        self.pin_tasks_calls: list[list[dict]] = []
        self.create_project_calls: list[dict] = []
        self.update_project_calls: list[dict] = []
        self.delete_project_calls: list[str] = []
        self._folders: list[ProjectGroup] = []
        self._folders_by_id: dict[str, ProjectGroup] = {}
        self.create_folder_calls: list[str] = []
        self.rename_folder_calls: list[tuple[str, str]] = []
        self.delete_folder_calls: list[str] = []
        self._columns_by_project: dict[str, list[Column]] = {}
        self.create_column_calls: list[dict] = []
        self.update_column_calls: list[dict] = []
        self.delete_column_calls: list[tuple[str, str]] = []
        self._tags: list[Tag] = []
        self._tags_by_name: dict[str, Tag] = {}
        self.create_tag_calls: list[dict] = []
        self.update_tag_calls: list[dict] = []
        self.delete_tag_calls: list[str] = []
        self.rename_tag_calls: list[tuple[str, str]] = []
        self.merge_tags_calls: list[tuple[str, str]] = []
        self._habits: dict[str, SimpleNamespace] = {}
        self.create_habit_calls: list[dict] = []
        self.update_habit_calls: list[dict] = []
        self.delete_habit_calls: list[str] = []
        self.checkin_habit_calls: list[dict] = []
        self.archive_habit_calls: list[str] = []
        self.unarchive_habit_calls: list[str] = []
        self.checkin_habits_calls: list[list[dict]] = []

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

    async def delete_task(self, task_id: str, project_id: str) -> None:
        self.delete_task_calls.append((task_id, project_id))
        self._tasks_by_id.pop(task_id, None)

    async def move_task(self, task_id: str, from_project_id: str, to_project_id: str) -> None:
        self.move_task_calls.append((task_id, from_project_id, to_project_id))
        task = self._tasks_by_id[task_id]
        task.project_id = to_project_id
        self._tasks_by_id[task_id] = task

    async def make_subtask(self, task_id: str, parent_id: str, project_id: str) -> None:
        self.make_subtask_calls.append((task_id, parent_id, project_id))
        task = self._tasks_by_id[task_id]
        task.parent_id = parent_id

    async def unparent_subtask(self, task_id: str, project_id: str) -> None:
        self.unparent_subtask_calls.append((task_id, project_id))
        task = self._tasks_by_id[task_id]
        task.parent_id = None

    async def pin_task(self, task_id: str, project_id: str) -> Task:
        self.pin_task_calls.append((task_id, project_id))
        task = self._tasks_by_id[task_id]
        task.pinned_time = datetime.now(UTC)
        return task

    async def unpin_task(self, task_id: str, project_id: str) -> Task:
        self.unpin_task_calls.append((task_id, project_id))
        task = self._tasks_by_id[task_id]
        task.pinned_time = None
        return task

    async def move_task_to_column(self, task_id: str, project_id: str, column_id: str | None) -> Task:
        self.move_task_to_column_calls.append((task_id, project_id, column_id))
        task = self._tasks_by_id[task_id]
        task.column_id = column_id
        return task

    async def update_task(self, task: Task) -> Task:
        self.update_task_calls.append(task)
        self._tasks_by_id[task.id] = task
        return task

    async def quick_add(self, text: str, project_id: str | None = None) -> Task:
        self.quick_add_calls.append((text, project_id))
        project = project_id or self.inbox_id
        return await self.create_task(title=text, project_id=project)

    async def search_tasks(self, query: str) -> list[Task]:
        query_lower = query.lower()
        return [
            task for task in self._tasks
            if (task.title and query_lower in task.title.lower())
            or (task.content and query_lower in task.content.lower())
        ]

    async def get_tasks_by_tag(self, tag_name: str) -> list[Task]:
        tag_lower = tag_name.lower()
        return [
            task for task in self._tasks
            if any(tag.lower() == tag_lower for tag in (task.tags or []))
        ]

    async def get_tasks_by_priority(self, priority: int | str) -> list[Task]:
        priority_value = 0
        if isinstance(priority, str):
            mapping = {"none": 0, "low": 1, "medium": 3, "high": 5}
            priority_value = mapping[priority]
        else:
            priority_value = priority
        return [task for task in self._tasks if int(task.priority) == int(priority_value)]

    async def get_today_tasks(self) -> list[Task]:
        today = datetime.now(UTC).date()
        return [task for task in self._tasks if task.due_date and task.due_date.date() == today]

    async def get_overdue_tasks(self) -> list[Task]:
        today = datetime.now(UTC).date()
        return [
            task for task in self._tasks
            if task.due_date and task.due_date.date() < today and int(task.status) == 0
        ]

    async def get_completed_tasks(self, days: int = 7, limit: int = 100) -> list[Task]:
        del days
        completed = [task for task in self._tasks if int(task.status) in (1, 2)]
        return completed[:limit]

    async def get_abandoned_tasks(self, days: int = 7, limit: int = 100) -> list[Task]:
        del days
        abandoned = [task for task in self._tasks if int(task.status) == -1]
        return abandoned[:limit]

    async def get_deleted_tasks(self, limit: int = 100) -> list[Task]:
        return self._tasks[:limit]

    async def create_tasks(self, tasks: list[dict]) -> list[Task]:
        self.create_tasks_calls.append(tasks)
        created: list[Task] = []
        for idx, spec in enumerate(tasks, start=1):
            task = Task(
                id=f"batch-created-{idx}",
                project_id=spec.get("project_id", self.inbox_id),
                title=spec["title"],
                content=spec.get("content"),
                priority=int(spec.get("priority", 0)),
                status=0,
                tags=spec.get("tags", []),
            )
            self._tasks.append(task)
            self._tasks_by_id[task.id] = task
            created.append(task)
        return created

    async def update_tasks(self, updates: list[dict]) -> dict:
        self.update_tasks_calls.append(updates)
        return {"id2etag": {"ok": "etag"}, "id2error": {}}

    async def delete_tasks(self, task_ids: list[tuple[str, str]]) -> dict:
        self.delete_tasks_calls.append(task_ids)
        return {"id2etag": {task_id: "etag" for task_id, _ in task_ids}, "id2error": {}}

    async def complete_tasks(self, task_ids: list[tuple[str, str]]) -> dict:
        self.complete_tasks_calls.append(task_ids)
        return {"id2etag": {task_id: "etag" for task_id, _ in task_ids}, "id2error": {}}

    async def move_tasks(self, moves: list[dict]) -> list[dict]:
        self.move_tasks_calls.append(moves)
        return moves

    async def set_task_parents(self, assignments: list[dict]) -> list[dict]:
        self.set_task_parents_calls.append(assignments)
        return assignments

    async def unparent_tasks(self, tasks: list[dict]) -> list[dict]:
        self.unparent_tasks_calls.append(tasks)
        return tasks

    async def pin_tasks(self, pin_operations: list[dict]) -> list[Task]:
        self.pin_tasks_calls.append(pin_operations)
        result: list[Task] = []
        for operation in pin_operations:
            task = self._tasks_by_id[operation["task_id"]]
            task.pinned_time = datetime.now(UTC) if operation.get("pin", True) else None
            result.append(task)
        return result

    async def get_all_projects(self) -> list[Project]:
        return self._projects

    async def get_project(self, project_id: str) -> Project:
        return self._projects_by_id[project_id]

    async def get_project_tasks(self, project_id: str) -> ProjectData:
        project = self._projects_by_id[project_id]
        tasks = [task for task in self._tasks if task.project_id == project_id]
        columns = [
            Column(id=f"{project_id}-col-1", project_id=project_id, name="Backlog", sort_order=0),
            Column(id=f"{project_id}-col-2", project_id=project_id, name="Doing", sort_order=1),
        ]
        return ProjectData(project=project, tasks=tasks, columns=columns)

    async def create_project(
        self,
        name: str,
        *,
        color: str | None = None,
        kind: str = "TASK",
        view_mode: str = "list",
        folder_id: str | None = None,
    ) -> Project:
        self.create_project_calls.append({
            "name": name,
            "color": color,
            "kind": kind,
            "view_mode": view_mode,
            "folder_id": folder_id,
        })
        project = Project(
            id=f"project-new-{len(self._projects) + 1}",
            name=name,
            color=color,
            kind=kind,
            view_mode=view_mode,
            group_id=folder_id,
            closed=False,
        )
        self._projects.append(project)
        self._projects_by_id[project.id] = project
        return project

    async def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        folder_id: str | None = None,
    ) -> Project:
        self.update_project_calls.append({
            "project_id": project_id,
            "name": name,
            "color": color,
            "folder_id": folder_id,
        })
        project = self._projects_by_id[project_id]
        if name is not None:
            project.name = name
        if color is not None:
            project.color = color
        if folder_id is not None:
            project.group_id = None if folder_id == "NONE" else folder_id
        self._projects_by_id[project_id] = project
        return project

    async def delete_project(self, project_id: str) -> None:
        self.delete_project_calls.append(project_id)
        self._projects_by_id.pop(project_id, None)
        self._projects = [project for project in self._projects if project.id != project_id]

    async def get_status(self) -> _Status:
        return _Status(self.inbox_id)

    async def get_profile(self) -> dict:
        return {"username": "test-user", "email": "test@example.com"}

    async def get_statistics(self) -> dict:
        return {"completed_tasks": 42, "focus_minutes": 120}

    async def get_preferences(self) -> dict:
        return {"timeZone": "Europe/Warsaw", "weekStartDay": 1}

    async def get_focus_heatmap(
        self,
        start_date=None,
        end_date=None,
        days: int = 30,
    ) -> list[dict]:
        del start_date, end_date, days
        return [
            {"date": "2026-02-01", "value": 2},
            {"date": "2026-02-02", "value": 1},
        ]

    async def get_focus_by_tag(
        self,
        start_date=None,
        end_date=None,
        days: int = 30,
    ) -> dict[str, int]:
        del start_date, end_date, days
        return {"work": 1500, "study": 2400}

    async def get_all_habits(self) -> list[SimpleNamespace]:
        return list(self._habits.values())

    async def get_habit(self, habit_id: str) -> SimpleNamespace:
        return self._habits[habit_id]

    async def get_habit_sections(self) -> list[dict]:
        return [
            {"id": "_morning", "name": "_morning"},
            {"id": "_night", "name": "_night"},
        ]

    async def get_habit_preferences(self) -> dict:
        return {"showInCalendar": True, "enabled": True}

    async def create_habit(self, name: str, **kwargs) -> SimpleNamespace:
        self.create_habit_calls.append({"name": name, **kwargs})
        habit_id = f"habit-{len(self._habits) + 1}"
        habit = SimpleNamespace(
            id=habit_id,
            name=name,
            habit_type=kwargs.get("habit_type", "Boolean"),
            goal=kwargs.get("goal", 1.0),
            status=0,
            total_checkins=0,
        )
        self._habits[habit_id] = habit
        return habit

    async def update_habit(self, habit_id: str, **kwargs) -> SimpleNamespace:
        self.update_habit_calls.append({"habit_id": habit_id, **kwargs})
        habit = self._habits[habit_id]
        for key, value in kwargs.items():
            if value is not None:
                setattr(habit, key, value)
        self._habits[habit_id] = habit
        return habit

    async def delete_habit(self, habit_id: str) -> None:
        self.delete_habit_calls.append(habit_id)
        self._habits.pop(habit_id, None)

    async def checkin_habit(self, habit_id: str, value: float = 1.0, checkin_date=None) -> SimpleNamespace:
        self.checkin_habit_calls.append({
            "habit_id": habit_id,
            "value": value,
            "checkin_date": checkin_date,
        })
        habit = self._habits[habit_id]
        habit.total_checkins = getattr(habit, "total_checkins", 0) + 1
        return habit

    async def archive_habit(self, habit_id: str) -> SimpleNamespace:
        self.archive_habit_calls.append(habit_id)
        habit = self._habits[habit_id]
        habit.status = 2
        return habit

    async def unarchive_habit(self, habit_id: str) -> SimpleNamespace:
        self.unarchive_habit_calls.append(habit_id)
        habit = self._habits[habit_id]
        habit.status = 0
        return habit

    async def get_habit_checkins(self, habit_ids: list[str], after_stamp: int = 0) -> dict:
        del after_stamp
        return {
            habit_id: [{"habit_id": habit_id, "checkin_stamp": 20260209, "value": 1.0}]
            for habit_id in habit_ids
        }

    async def checkin_habits(self, checkins: list[dict]) -> dict:
        self.checkin_habits_calls.append(checkins)
        result: dict[str, SimpleNamespace] = {}
        for item in checkins:
            habit = await self.checkin_habit(
                item["habit_id"],
                value=item.get("value", 1.0),
                checkin_date=item.get("checkin_date"),
            )
            result[item["habit_id"]] = habit
        return result

    async def get_all_folders(self) -> list[ProjectGroup]:
        return self._folders

    async def create_folder(self, name: str) -> ProjectGroup:
        self.create_folder_calls.append(name)
        folder = ProjectGroup(
            id=f"folder-{len(self._folders) + 1}",
            name=name,
            view_mode="list",
            sort_order=len(self._folders),
            deleted=0,
            show_all=True,
        )
        self._folders.append(folder)
        self._folders_by_id[folder.id] = folder
        return folder

    async def rename_folder(self, folder_id: str, name: str) -> ProjectGroup:
        self.rename_folder_calls.append((folder_id, name))
        folder = self._folders_by_id[folder_id]
        folder.name = name
        self._folders_by_id[folder_id] = folder
        return folder

    async def delete_folder(self, folder_id: str) -> None:
        self.delete_folder_calls.append(folder_id)
        self._folders_by_id.pop(folder_id, None)
        self._folders = [folder for folder in self._folders if folder.id != folder_id]

    async def get_columns(self, project_id: str) -> list[Column]:
        return self._columns_by_project.get(project_id, [])

    async def create_column(
        self,
        project_id: str,
        name: str,
        *,
        sort_order: int | None = None,
    ) -> Column:
        self.create_column_calls.append({
            "project_id": project_id,
            "name": name,
            "sort_order": sort_order,
        })
        columns = self._columns_by_project.setdefault(project_id, [])
        column = Column(
            id=f"{project_id}-col-{len(columns) + 1}",
            project_id=project_id,
            name=name,
            sort_order=sort_order if sort_order is not None else len(columns),
        )
        columns.append(column)
        return column

    async def update_column(
        self,
        column_id: str,
        project_id: str,
        *,
        name: str | None = None,
        sort_order: int | None = None,
    ) -> Column:
        self.update_column_calls.append({
            "column_id": column_id,
            "project_id": project_id,
            "name": name,
            "sort_order": sort_order,
        })
        columns = self._columns_by_project.setdefault(project_id, [])
        for column in columns:
            if column.id == column_id:
                if name is not None:
                    column.name = name
                if sort_order is not None:
                    column.sort_order = sort_order
                return column
        raise KeyError(column_id)

    async def delete_column(self, column_id: str, project_id: str) -> None:
        self.delete_column_calls.append((column_id, project_id))
        columns = self._columns_by_project.setdefault(project_id, [])
        self._columns_by_project[project_id] = [col for col in columns if col.id != column_id]

    async def get_all_tags(self) -> list[Tag]:
        return self._tags

    async def create_tag(
        self,
        name: str,
        *,
        color: str | None = None,
        parent: str | None = None,
    ) -> Tag:
        self.create_tag_calls.append({
            "name": name,
            "color": color,
            "parent": parent,
        })
        tag = Tag(name=name, label=name, color=color, parent=parent)
        self._tags_by_name[name] = tag
        self._tags = list(self._tags_by_name.values())
        return tag

    async def update_tag(
        self,
        name: str,
        *,
        color: str | None = None,
        parent: str | None = None,
    ) -> Tag:
        self.update_tag_calls.append({
            "name": name,
            "color": color,
            "parent": parent,
        })
        tag = self._tags_by_name[name]
        if color is not None:
            tag.color = color
        tag.parent = parent
        self._tags_by_name[name] = tag
        self._tags = list(self._tags_by_name.values())
        return tag

    async def delete_tag(self, name: str) -> None:
        self.delete_tag_calls.append(name)
        self._tags_by_name.pop(name, None)
        self._tags = list(self._tags_by_name.values())

    async def rename_tag(self, old_name: str, new_name: str) -> None:
        self.rename_tag_calls.append((old_name, new_name))
        tag = self._tags_by_name.pop(old_name)
        tag.name = new_name
        tag.label = new_name
        self._tags_by_name[new_name] = tag
        self._tags = list(self._tags_by_name.values())

    async def merge_tags(self, source: str, target: str) -> None:
        self.merge_tags_calls.append((source, target))
        self._tags_by_name.pop(source, None)
        self._tags = list(self._tags_by_name.values())


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


@pytest.mark.asyncio
async def test_projects_get_returns_single_project_json(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "project-a")
    projects = [
        Project(id="project-a", name="Alpha", kind="TASK", view_mode="list"),
        Project(id="project-b", name="Beta", kind="NOTE", view_mode="kanban"),
    ]
    client = _FakeClient(projects=projects)

    args = Namespace(
        command="projects",
        projects_command="get",
        project_id="project-b",
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["project"]["id"] == "project-b"
    assert output["project"]["name"] == "Beta"


@pytest.mark.asyncio
async def test_projects_data_includes_tasks_and_columns(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "project-a")
    monkeypatch.setenv("TZ", "UTC")

    projects = [
        Project(id="project-a", name="Alpha", kind="TASK", view_mode="list"),
    ]
    tasks = [
        Task(
            id="task-1",
            project_id="project-a",
            title="Task one",
            priority=0,
            status=0,
            tags=[],
        ),
    ]
    client = _FakeClient(projects=projects, tasks=tasks)

    args = Namespace(
        command="projects",
        projects_command="data",
        project_id="project-a",
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["data"]["project"]["id"] == "project-a"
    assert output["data"]["task_count"] == 1
    assert output["data"]["column_count"] == 2


@pytest.mark.asyncio
async def test_projects_create_passes_fields(capsys) -> None:
    client = _FakeClient(projects=[])
    args = Namespace(
        command="projects",
        projects_command="create",
        name="Roadmap",
        color="#123456",
        kind="NOTE",
        view_mode="kanban",
        folder_id="folder-1",
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0
    assert client.create_project_calls == [{
        "name": "Roadmap",
        "color": "#123456",
        "kind": "NOTE",
        "view_mode": "kanban",
        "folder_id": "folder-1",
    }]

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["project"]["name"] == "Roadmap"


@pytest.mark.asyncio
async def test_projects_update_can_remove_folder(monkeypatch, capsys) -> None:
    monkeypatch.setenv("TICKTICK_CURRENT_PROJECT_ID", "project-a")
    projects = [
        Project(id="project-a", name="Alpha", group_id="folder-x"),
    ]
    client = _FakeClient(projects=projects)
    args = Namespace(
        command="projects",
        projects_command="update",
        project_id="project-a",
        name="Alpha Updated",
        color=None,
        folder_id=None,
        remove_folder=True,
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0
    assert client.update_project_calls == [{
        "project_id": "project-a",
        "name": "Alpha Updated",
        "color": None,
        "folder_id": "NONE",
    }]

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["project"]["name"] == "Alpha Updated"
    assert output["project"]["folder_id"] is None


@pytest.mark.asyncio
async def test_projects_delete_invokes_client(capsys) -> None:
    projects = [Project(id="project-a", name="Alpha")]
    client = _FakeClient(projects=projects)
    args = Namespace(
        command="projects",
        projects_command="delete",
        project_id="project-a",
        json=True,
    )

    exit_code = await _run_projects_command(client, args)
    assert exit_code == 0
    assert client.delete_project_calls == ["project-a"]

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["action"] == "delete"


@pytest.mark.asyncio
async def test_folders_create_list_rename_delete_flow(capsys) -> None:
    client = _FakeClient()

    create_args = Namespace(
        command="folders",
        folders_command="create",
        name="Personal",
        json=True,
    )
    create_exit = await _run_folders_command(client, create_args)
    assert create_exit == 0
    created_output = json.loads(capsys.readouterr().out)
    folder_id = created_output["folder"]["id"]
    assert created_output["folder"]["name"] == "Personal"

    list_args = Namespace(
        command="folders",
        folders_command="list",
        json=True,
    )
    list_exit = await _run_folders_command(client, list_args)
    assert list_exit == 0
    list_output = json.loads(capsys.readouterr().out)
    assert list_output["count"] == 1
    assert list_output["folders"][0]["id"] == folder_id

    rename_args = Namespace(
        command="folders",
        folders_command="rename",
        folder_id=folder_id,
        name="Personal Updated",
        json=True,
    )
    rename_exit = await _run_folders_command(client, rename_args)
    assert rename_exit == 0
    rename_output = json.loads(capsys.readouterr().out)
    assert rename_output["folder"]["name"] == "Personal Updated"
    assert client.rename_folder_calls == [(folder_id, "Personal Updated")]

    delete_args = Namespace(
        command="folders",
        folders_command="delete",
        folder_id=folder_id,
        json=True,
    )
    delete_exit = await _run_folders_command(client, delete_args)
    assert delete_exit == 0
    delete_output = json.loads(capsys.readouterr().out)
    assert delete_output["success"] is True
    assert delete_output["action"] == "delete"
    assert client.delete_folder_calls == [folder_id]


@pytest.mark.asyncio
async def test_columns_create_list_update_delete_flow(capsys) -> None:
    client = _FakeClient()
    project_id = "project-1"

    create_args = Namespace(
        command="columns",
        columns_command="create",
        project_id=project_id,
        name="Backlog",
        sort_order=0,
        json=True,
    )
    create_exit = await _run_columns_command(client, create_args)
    assert create_exit == 0
    create_output = json.loads(capsys.readouterr().out)
    column_id = create_output["column"]["id"]
    assert create_output["column"]["name"] == "Backlog"

    list_args = Namespace(
        command="columns",
        columns_command="list",
        project_id=project_id,
        json=True,
    )
    list_exit = await _run_columns_command(client, list_args)
    assert list_exit == 0
    list_output = json.loads(capsys.readouterr().out)
    assert list_output["count"] == 1
    assert list_output["columns"][0]["id"] == column_id

    update_args = Namespace(
        command="columns",
        columns_command="update",
        column_id=column_id,
        project_id=project_id,
        name="In Progress",
        sort_order=2,
        json=True,
    )
    update_exit = await _run_columns_command(client, update_args)
    assert update_exit == 0
    update_output = json.loads(capsys.readouterr().out)
    assert update_output["column"]["name"] == "In Progress"
    assert update_output["column"]["sort_order"] == 2

    delete_args = Namespace(
        command="columns",
        columns_command="delete",
        column_id=column_id,
        project_id=project_id,
        json=True,
    )
    delete_exit = await _run_columns_command(client, delete_args)
    assert delete_exit == 0
    delete_output = json.loads(capsys.readouterr().out)
    assert delete_output["success"] is True
    assert delete_output["action"] == "delete"
    assert client.delete_column_calls == [(column_id, project_id)]


@pytest.mark.asyncio
async def test_tags_full_lifecycle_flow(capsys) -> None:
    client = _FakeClient()

    create_args = Namespace(
        command="tags",
        tags_command="create",
        name="work",
        color="#ff0000",
        parent=None,
        json=True,
    )
    create_exit = await _run_tags_command(client, create_args)
    assert create_exit == 0
    create_output = json.loads(capsys.readouterr().out)
    assert create_output["success"] is True
    assert create_output["tag"]["name"] == "work"

    list_args = Namespace(
        command="tags",
        tags_command="list",
        json=True,
    )
    list_exit = await _run_tags_command(client, list_args)
    assert list_exit == 0
    list_output = json.loads(capsys.readouterr().out)
    assert list_output["count"] == 1
    assert list_output["tags"][0]["name"] == "work"

    update_args = Namespace(
        command="tags",
        tags_command="update",
        name="work",
        color="#00ff00",
        parent="root",
        clear_parent=False,
        json=True,
    )
    update_exit = await _run_tags_command(client, update_args)
    assert update_exit == 0
    update_output = json.loads(capsys.readouterr().out)
    assert update_output["tag"]["color"] == "#00ff00"
    assert update_output["tag"]["parent"] == "root"

    rename_args = Namespace(
        command="tags",
        tags_command="rename",
        old_name="work",
        new_name="work-renamed",
        json=True,
    )
    rename_exit = await _run_tags_command(client, rename_args)
    assert rename_exit == 0
    rename_output = json.loads(capsys.readouterr().out)
    assert rename_output["action"] == "rename"
    assert rename_output["new_name"] == "work-renamed"

    create_second_args = Namespace(
        command="tags",
        tags_command="create",
        name="target",
        color=None,
        parent=None,
        json=True,
    )
    create_second_exit = await _run_tags_command(client, create_second_args)
    assert create_second_exit == 0
    _ = capsys.readouterr().out

    merge_args = Namespace(
        command="tags",
        tags_command="merge",
        source="work-renamed",
        target="target",
        json=True,
    )
    merge_exit = await _run_tags_command(client, merge_args)
    assert merge_exit == 0
    merge_output = json.loads(capsys.readouterr().out)
    assert merge_output["action"] == "merge"
    assert client.merge_tags_calls == [("work-renamed", "target")]

    delete_args = Namespace(
        command="tags",
        tags_command="delete",
        name="target",
        json=True,
    )
    delete_exit = await _run_tags_command(client, delete_args)
    assert delete_exit == 0
    delete_output = json.loads(capsys.readouterr().out)
    assert delete_output["action"] == "delete"
    assert client.delete_tag_calls == ["target"]


@pytest.mark.asyncio
async def test_user_commands_return_json(capsys) -> None:
    client = _FakeClient()

    profile_args = Namespace(command="user", user_command="profile", json=True)
    status_args = Namespace(command="user", user_command="status", json=True)
    statistics_args = Namespace(command="user", user_command="statistics", json=True)
    preferences_args = Namespace(command="user", user_command="preferences", json=True)

    assert await _run_user_command(client, profile_args) == 0
    profile_output = json.loads(capsys.readouterr().out)
    assert profile_output["profile"]["username"] == "test-user"

    assert await _run_user_command(client, status_args) == 0
    status_output = json.loads(capsys.readouterr().out)
    assert status_output["status"]["inbox_id"] == "inbox-default"

    assert await _run_user_command(client, statistics_args) == 0
    statistics_output = json.loads(capsys.readouterr().out)
    assert statistics_output["statistics"]["completed_tasks"] == 42

    assert await _run_user_command(client, preferences_args) == 0
    preferences_output = json.loads(capsys.readouterr().out)
    assert preferences_output["preferences"]["timeZone"] == "Europe/Warsaw"


@pytest.mark.asyncio
async def test_focus_commands_return_json() -> None:
    client = _FakeClient()

    heatmap_args = Namespace(
        command="focus",
        focus_command="heatmap",
        from_date=None,
        to_date=None,
        days=14,
        json=True,
    )
    by_tag_args = Namespace(
        command="focus",
        focus_command="by-tag",
        from_date="2026-02-01",
        to_date="2026-02-09",
        days=14,
        json=True,
    )

    from io import StringIO
    import contextlib

    with contextlib.redirect_stdout(StringIO()) as output:
        heatmap_exit = await _run_focus_command(client, heatmap_args)
    heatmap_payload = json.loads(output.getvalue())
    assert heatmap_exit == 0
    assert heatmap_payload["count"] == 2
    assert heatmap_payload["days"] == 14

    with contextlib.redirect_stdout(StringIO()) as output:
        by_tag_exit = await _run_focus_command(client, by_tag_args)
    by_tag_payload = json.loads(output.getvalue())
    assert by_tag_exit == 0
    assert by_tag_payload["tag_count"] == 2
    assert by_tag_payload["focus_by_tag"]["work"] == 1500


@pytest.mark.asyncio
async def test_habits_lifecycle_and_checkins(capsys, tmp_path) -> None:
    client = _FakeClient()

    create_args = Namespace(
        command="habits",
        habits_command="create",
        name="Read 20 pages",
        habit_type="Boolean",
        goal=1.0,
        step=0.0,
        unit="Count",
        icon="habit_daily_check_in",
        color="#97E38B",
        section_id=None,
        repeat_rule="RRULE:FREQ=DAILY",
        reminders="08:00,20:00",
        target_days=30,
        encouragement="Keep going",
        json=True,
    )
    create_exit = await _run_habits_command(client, create_args)
    assert create_exit == 0
    create_payload = json.loads(capsys.readouterr().out)
    habit_id = create_payload["habit"]["id"]
    assert create_payload["habit"]["name"] == "Read 20 pages"

    list_args = Namespace(command="habits", habits_command="list", json=True)
    list_exit = await _run_habits_command(client, list_args)
    assert list_exit == 0
    list_payload = json.loads(capsys.readouterr().out)
    assert list_payload["count"] == 1

    get_args = Namespace(command="habits", habits_command="get", habit_id=habit_id, json=True)
    get_exit = await _run_habits_command(client, get_args)
    assert get_exit == 0
    get_payload = json.loads(capsys.readouterr().out)
    assert get_payload["habit"]["id"] == habit_id

    sections_args = Namespace(command="habits", habits_command="sections", json=True)
    sections_exit = await _run_habits_command(client, sections_args)
    assert sections_exit == 0
    sections_payload = json.loads(capsys.readouterr().out)
    assert sections_payload["count"] == 2

    preferences_args = Namespace(command="habits", habits_command="preferences", json=True)
    preferences_exit = await _run_habits_command(client, preferences_args)
    assert preferences_exit == 0
    preferences_payload = json.loads(capsys.readouterr().out)
    assert preferences_payload["preferences"]["enabled"] is True

    update_args = Namespace(
        command="habits",
        habits_command="update",
        habit_id=habit_id,
        name="Read 30 pages",
        goal=None,
        step=None,
        unit=None,
        icon=None,
        color=None,
        section_id=None,
        repeat_rule=None,
        reminders=None,
        target_days=None,
        encouragement=None,
        json=True,
    )
    update_exit = await _run_habits_command(client, update_args)
    assert update_exit == 0
    update_payload = json.loads(capsys.readouterr().out)
    assert update_payload["habit"]["name"] == "Read 30 pages"

    checkin_args = Namespace(
        command="habits",
        habits_command="checkin",
        habit_id=habit_id,
        value=1.0,
        checkin_date="2026-02-09",
        json=True,
    )
    checkin_exit = await _run_habits_command(client, checkin_args)
    assert checkin_exit == 0
    checkin_payload = json.loads(capsys.readouterr().out)
    assert checkin_payload["habit"]["total_checkins"] == 1

    checkins_args = Namespace(
        command="habits",
        habits_command="checkins",
        habit_ids=[habit_id],
        after_stamp=0,
        json=True,
    )
    checkins_exit = await _run_habits_command(client, checkins_args)
    assert checkins_exit == 0
    checkins_payload = json.loads(capsys.readouterr().out)
    assert checkins_payload["habit_count"] == 1
    assert habit_id in checkins_payload["checkins"]

    batch_file = tmp_path / "habit_batch_checkin.json"
    batch_file.write_text(
        json.dumps([{"habit_id": habit_id, "value": 1.0, "checkin_date": "2026-02-10"}]),
        encoding="utf-8",
    )
    batch_args = Namespace(
        command="habits",
        habits_command="batch-checkin",
        file=str(batch_file),
        json=True,
    )
    batch_exit = await _run_habits_command(client, batch_args)
    assert batch_exit == 0
    batch_payload = json.loads(capsys.readouterr().out)
    assert batch_payload["success"] is True
    assert batch_payload["count"] == 1

    archive_args = Namespace(command="habits", habits_command="archive", habit_id=habit_id, json=True)
    archive_exit = await _run_habits_command(client, archive_args)
    assert archive_exit == 0
    archive_payload = json.loads(capsys.readouterr().out)
    assert archive_payload["habit"]["status"] == 2

    unarchive_args = Namespace(command="habits", habits_command="unarchive", habit_id=habit_id, json=True)
    unarchive_exit = await _run_habits_command(client, unarchive_args)
    assert unarchive_exit == 0
    unarchive_payload = json.loads(capsys.readouterr().out)
    assert unarchive_payload["habit"]["status"] == 0

    delete_args = Namespace(command="habits", habits_command="delete", habit_id=habit_id, json=True)
    delete_exit = await _run_habits_command(client, delete_args)
    assert delete_exit == 0
    delete_payload = json.loads(capsys.readouterr().out)
    assert delete_payload["action"] == "delete"


@pytest.mark.asyncio
async def test_tasks_update_sets_fields(monkeypatch, capsys) -> None:
    monkeypatch.delenv("TICKTICK_CURRENT_PROJECT_ID", raising=False)
    monkeypatch.setenv("TZ", "UTC")

    task = Task(
        id="task-upd",
        project_id="proj-1",
        title="Old title",
        content="Old content",
        desc="Old desc",
        priority=0,
        status=0,
        tags=["old"],
    )
    client = _FakeClient(tasks=[task])

    args = Namespace(
        command="tasks",
        tasks_command="update",
        task_id="task-upd",
        project_id=None,
        title="New title",
        content="New content",
        description="New desc",
        kind="NOTE",
        priority="high",
        start=None,
        clear_start=False,
        due=None,
        clear_due=False,
        tags="work,urgent",
        clear_tags=False,
        recurrence="RRULE:FREQ=DAILY",
        clear_recurrence=False,
        time_zone="Europe/Warsaw",
        all_day=False,
        timed=False,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert len(client.update_task_calls) == 1

    updated = client.update_task_calls[0]
    assert updated.title == "New title"
    assert updated.content == "New content"
    assert updated.desc == "New desc"
    assert updated.kind == "NOTE"
    assert int(updated.priority) == 5
    assert updated.tags == ["work", "urgent"]
    assert updated.repeat_flag == "RRULE:FREQ=DAILY"
    assert updated.time_zone == "Europe/Warsaw"

    output = json.loads(capsys.readouterr().out)
    assert output["success"] is True
    assert output["task"]["id"] == "task-upd"


@pytest.mark.asyncio
async def test_tasks_delete_resolves_project_from_task(capsys) -> None:
    task = Task(
        id="task-del",
        project_id="proj-del",
        title="Delete me",
        priority=0,
        status=0,
        tags=[],
    )
    client = _FakeClient(tasks=[task])

    args = Namespace(
        command="tasks",
        tasks_command="delete",
        task_id="task-del",
        project_id=None,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.delete_task_calls == [("task-del", "proj-del")]

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "delete"


@pytest.mark.asyncio
async def test_tasks_move_auto_resolves_from_project(capsys) -> None:
    task = Task(
        id="task-move",
        project_id="proj-from",
        title="Move me",
        priority=0,
        status=0,
        tags=[],
    )
    client = _FakeClient(tasks=[task])

    args = Namespace(
        command="tasks",
        tasks_command="move",
        task_id="task-move",
        from_project_id=None,
        to_project_id="proj-to",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.move_task_calls == [("task-move", "proj-from", "proj-to")]

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "move"


@pytest.mark.asyncio
async def test_tasks_search_can_filter_project(capsys) -> None:
    tasks = [
        Task(
            id="search-1",
            project_id="p1",
            title="Find me",
            content="needle",
            priority=0,
            status=0,
            tags=[],
        ),
        Task(
            id="search-2",
            project_id="p2",
            title="Find me too",
            content="needle",
            priority=0,
            status=0,
            tags=[],
        ),
    ]
    client = _FakeClient(tasks=tasks)

    args = Namespace(
        command="tasks",
        tasks_command="search",
        query="needle",
        project_id="p1",
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 1
    assert output["tasks"][0]["id"] == "search-1"


@pytest.mark.asyncio
async def test_tasks_by_priority_accepts_named_priority(capsys) -> None:
    tasks = [
        Task(
            id="prio-high",
            project_id="p1",
            title="High",
            priority=5,
            status=0,
            tags=[],
        ),
        Task(
            id="prio-low",
            project_id="p1",
            title="Low",
            priority=1,
            status=0,
            tags=[],
        ),
    ]
    client = _FakeClient(tasks=tasks)

    args = Namespace(
        command="tasks",
        tasks_command="by-priority",
        priority="high",
        project_id=None,
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0

    output = json.loads(capsys.readouterr().out)
    assert output["count"] == 1
    assert output["tasks"][0]["id"] == "prio-high"


@pytest.mark.asyncio
async def test_tasks_batch_delete_accepts_object_entries(tmp_path, capsys) -> None:
    client = _FakeClient()
    payload = [
        {"task_id": "task-1", "project_id": "proj-1"},
        {"task_id": "task-2", "project_id": "proj-2"},
    ]
    file_path = tmp_path / "batch_delete.json"
    file_path.write_text(json.dumps(payload), encoding="utf-8")

    args = Namespace(
        command="tasks",
        tasks_command="batch-delete",
        file=str(file_path),
        json=True,
    )

    exit_code = await _run_tasks_command(client, args)
    assert exit_code == 0
    assert client.delete_tasks_calls == [[("task-1", "proj-1"), ("task-2", "proj-2")]]

    output = json.loads(capsys.readouterr().out)
    assert output["action"] == "batch-delete"


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

# ticktick-cli

Standalone command-line interface for TickTick, powered by
[`ticktick-sdk`](https://pypi.org/project/ticktick-sdk/).

This repository contains only CLI code and depends on `ticktick-sdk` for API
and auth implementation.

## Progress Tracker

| Area | Status | Notes |
|------|--------|-------|
| Tasks | Done | Full single-task + batch task command surface implemented |
| Projects | In Progress | `projects list` implemented |
| Folders | Planned | Not yet implemented in CLI commands |
| Columns | Planned | Not yet implemented in CLI commands |
| Tags | Planned | Not yet implemented in CLI commands |
| Habits | Planned | Not yet implemented in CLI commands |
| User | Planned | Not yet implemented in CLI commands |
| Focus | Planned | Not yet implemented in CLI commands |

## Installation

```bash
pip install ticktick-cli
```

## Global Usage

```bash
ticktick --help
ticktick --version
ticktick --json <command>
```

`--json` is supported on data commands and produces machine-friendly output.

## Core Commands

```bash
ticktick server
ticktick server --host ticktick.com
ticktick server --enabledModules tasks,projects
ticktick server --enabledTools ticktick_list_tasks,ticktick_create_tasks

ticktick auth
ticktick auth --manual
```

## Task Commands

### Read and Query

```bash
ticktick tasks list [--project PROJECT_ID] [--due YYYY-MM-DD]
ticktick tasks get TASK_ID [--project PROJECT_ID]
ticktick tasks search QUERY [--project PROJECT_ID]
ticktick tasks by-tag TAG [--project PROJECT_ID]
ticktick tasks by-priority PRIORITY [--project PROJECT_ID]
ticktick tasks today [--project PROJECT_ID]
ticktick tasks overdue [--project PROJECT_ID]
ticktick tasks completed [--days N] [--limit N] [--project PROJECT_ID]
ticktick tasks abandoned [--days N] [--limit N] [--project PROJECT_ID]
ticktick tasks deleted [--limit N] [--project PROJECT_ID]
```

`PRIORITY` accepts `none|low|medium|high|0|1|3|5`.

### Create

```bash
ticktick tasks add "Title" \
  [--project PROJECT_ID] \
  [--content TEXT] \
  [--description TEXT] \
  [--kind TEXT|NOTE|CHECKLIST] \
  [--start YYYY-MM-DD|ISO_DATETIME] \
  [--due YYYY-MM-DD|ISO_DATETIME] \
  [--priority none|low|medium|high] \
  [--tags tag1,tag2] \
  [--recurrence RRULE] \
  [--time-zone IANA_TZ] \
  [--all-day|--timed] \
  [--parent PARENT_TASK_ID] \
  [--reminders TRIGGER_1,TRIGGER_2]

ticktick tasks quick-add "Quick task title" [--project PROJECT_ID]
```

Examples:

```bash
ticktick tasks add "Pay rent" --due 2026-03-01 --priority high
ticktick tasks add "Write draft" --content "Outline + first pass"
ticktick tasks add "Standup notes" --kind NOTE --tags work,team
ticktick tasks quick-add "Buy coffee beans"
```

### Update and Lifecycle

```bash
ticktick tasks update TASK_ID \
  [--project PROJECT_ID] \
  [--title TEXT] \
  [--content TEXT] \
  [--description TEXT] \
  [--kind TEXT|NOTE|CHECKLIST] \
  [--priority none|low|medium|high] \
  [--start YYYY-MM-DD|ISO_DATETIME|--clear-start] \
  [--due YYYY-MM-DD|ISO_DATETIME|--clear-due] \
  [--tags tag1,tag2|--clear-tags] \
  [--recurrence RRULE|--clear-recurrence] \
  [--time-zone IANA_TZ] \
  [--all-day|--timed]

ticktick tasks done TASK_ID [--project PROJECT_ID]
ticktick tasks abandon TASK_ID [--project PROJECT_ID]
ticktick tasks delete TASK_ID [--project PROJECT_ID]
```

### Move, Parenting, and Pinning

```bash
ticktick tasks move TASK_ID --to-project PROJECT_ID [--from-project PROJECT_ID]
ticktick tasks subtask TASK_ID --parent PARENT_TASK_ID [--project PROJECT_ID]
ticktick tasks unparent TASK_ID [--project PROJECT_ID]
ticktick tasks pin TASK_ID [--project PROJECT_ID]
ticktick tasks unpin TASK_ID [--project PROJECT_ID]
ticktick tasks column TASK_ID [--project PROJECT_ID] (--column COLUMN_ID | --clear-column)
```

## Batch Task Commands

All batch commands read JSON arrays from `--file`.

```bash
ticktick tasks batch-create --file tasks_create.json
ticktick tasks batch-update --file tasks_update.json
ticktick tasks batch-delete --file tasks_delete.json
ticktick tasks batch-done --file tasks_complete.json
ticktick tasks batch-move --file tasks_move.json
ticktick tasks batch-parent --file tasks_parent.json
ticktick tasks batch-unparent --file tasks_unparent.json
ticktick tasks batch-pin --file tasks_pin.json
```

### Batch File Formats

`batch-create` expects an array of objects (`title` required):

```json
[
  {
    "title": "Task A",
    "project_id": "PROJECT_ID",
    "content": "notes",
    "priority": "high",
    "tags": ["work", "urgent"],
    "due_date": "2026-02-15T09:00:00+00:00"
  }
]
```

`batch-update` expects objects with `task_id` and `project_id`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID",
    "title": "Updated title",
    "priority": 3
  }
]
```

`batch-delete` and `batch-done` accept either format:

```json
[
  ["TASK_ID", "PROJECT_ID"],
  {"task_id": "TASK_ID_2", "project_id": "PROJECT_ID_2"}
]
```

`batch-move`:

```json
[
  {
    "task_id": "TASK_ID",
    "from_project_id": "FROM_PROJECT_ID",
    "to_project_id": "TO_PROJECT_ID"
  }
]
```

`batch-parent`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID",
    "parent_id": "PARENT_TASK_ID"
  }
]
```

`batch-unparent`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID"
  }
]
```

`batch-pin`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID",
    "pin": true
  }
]
```

## Project Commands

```bash
ticktick projects list
```

## Project Resolution Rules

When a task command needs project context and `--project` is omitted:

1. For commands that operate on an existing task (`done`, `abandon`, `delete`,
   `pin`, `unpin`, `column`, `update`, `subtask`, `unparent`, etc.), project is
   auto-resolved from the task itself.
2. For create/list-style commands, project resolves in this order:
   - explicit `--project`
   - `TICKTICK_CURRENT_PROJECT_ID`
   - account inbox project ID

## Timezone

Set `TZ` to an IANA timezone for due date parsing/filtering defaults:

```bash
export TZ=America/New_York
ticktick tasks list --due 2026-02-09
```

You can override per-command storage timezone with `--time-zone`.

## Required Environment Variables

These are read by `ticktick-sdk`:

- `TICKTICK_CLIENT_ID`
- `TICKTICK_CLIENT_SECRET`
- `TICKTICK_ACCESS_TOKEN`
- `TICKTICK_USERNAME`
- `TICKTICK_PASSWORD`

Optional:

- `TICKTICK_REDIRECT_URI`
- `TICKTICK_HOST`
- `TICKTICK_TIMEOUT`
- `TICKTICK_DEVICE_ID`
- `TICKTICK_CURRENT_PROJECT_ID`
- `TZ`

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Build

```bash
python3 -m pip install build
python3 -m build
```

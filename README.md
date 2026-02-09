# ticktick-cli

A standalone command-line interface for TickTick.

`ticktick-cli` gives you a scriptable interface for daily TickTick operations,
including tasks, projects, folders, columns, tags, habits, user info, focus
analytics, and full account sync payload access.

## Installation

```bash
pip install ticktick-cli
```

Python 3.11+ is required.

## Authentication Setup (Required)

This CLI needs both OAuth2 (V1 API) and account credentials (V2/session API).

1. Create an app at TickTick Developer Portal:
   `https://developer.ticktick.com/manage`
2. Set redirect URI in your TickTick app.
   Default is:
   `http://127.0.0.1:8080/callback`
3. Create a `.env` file in your working directory:

```bash
cp .env.example .env
```

4. Fill required values:

```dotenv
# OAuth app credentials (required)
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
TICKTICK_REDIRECT_URI=http://127.0.0.1:8080/callback
TICKTICK_ACCESS_TOKEN=

# TickTick account credentials (required for V2/session endpoints)
TICKTICK_USERNAME=you@example.com
TICKTICK_PASSWORD=your_password
```

5. Run OAuth flow to get `TICKTICK_ACCESS_TOKEN`:

```bash
ticktick auth
```

If you are on SSH/headless environment:

```bash
ticktick auth --manual
```

6. Save the generated token in `.env` as `TICKTICK_ACCESS_TOKEN`.
7. Verify connection:

```bash
ticktick projects list --json
```

## Quick Start

```bash
# List projects
ticktick projects list

# Create a task in inbox/current project
ticktick tasks add "Buy coffee" --priority medium

# Mark task complete
ticktick tasks done TASK_ID

# Show full sync payload (raw account state)
ticktick sync --json
```

## Global Usage

```bash
ticktick --help
ticktick --version
ticktick --json <command>
```

Notes:

- `--json` is supported on data commands.
- `auth` and `server` accept `--json` for consistency, but output remains
  interactive/text-oriented.

## Top-Level Commands

```bash
ticktick server [--enabledTools CSV] [--enabledModules CSV] [--host ticktick.com|dida365.com]
ticktick auth [--manual]
ticktick sync [--json]

ticktick tasks <action> ...
ticktick projects <action> ...
ticktick folders <action> ...
ticktick columns <action> ...
ticktick tags <action> ...
ticktick habits <action> ...
ticktick user <action> ...
ticktick focus <action> ...
```

## Command Reference

### Server

```bash
ticktick server
ticktick server --enabledModules tasks,projects
ticktick server --enabledTools ticktick_list_tasks,ticktick_create_tasks
ticktick server --host ticktick.com
```

### Auth

```bash
ticktick auth
ticktick auth --manual
```

### Sync

```bash
ticktick sync [--json]
```

Returns the raw full-account sync payload (`checkPoint`, projects, tags,
ordering blocks, task deltas, and more). Useful for diagnostics and backup-like
inspection.

### Tasks

#### Read and Query

```bash
ticktick tasks list [--project PROJECT_ID] [--due YYYY-MM-DD] [--json]
ticktick tasks get TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks search QUERY [--project PROJECT_ID] [--json]
ticktick tasks by-tag TAG_NAME [--project PROJECT_ID] [--json]
ticktick tasks by-priority PRIORITY [--project PROJECT_ID] [--json]
ticktick tasks today [--project PROJECT_ID] [--json]
ticktick tasks overdue [--project PROJECT_ID] [--json]
ticktick tasks completed [--days N] [--limit N] [--project PROJECT_ID] [--json]
ticktick tasks abandoned [--days N] [--limit N] [--project PROJECT_ID] [--json]
ticktick tasks deleted [--limit N] [--project PROJECT_ID] [--json]
```

`PRIORITY` accepts `none|low|medium|high|0|1|3|5`.
`--content` is task note/body text. `--description` maps to TickTick checklist
description field (`desc` in API payloads).

#### Create

```bash
ticktick tasks add TITLE \
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
  [--reminders TRIGGER_1,TRIGGER_2] \
  [--json]

ticktick tasks quick-add TEXT [--project PROJECT_ID] [--json]
```

#### Update and Lifecycle

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
  [--all-day|--timed] \
  [--json]

ticktick tasks done TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks abandon TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks delete TASK_ID [--project PROJECT_ID] [--json]
```

#### Move, Hierarchy, Pinning, Columns

```bash
ticktick tasks move TASK_ID --to-project PROJECT_ID [--from-project PROJECT_ID] [--json]
ticktick tasks subtask TASK_ID --parent PARENT_TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks unparent TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks pin TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks unpin TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks column TASK_ID [--project PROJECT_ID] (--column COLUMN_ID | --clear-column) [--json]
```

#### Batch Operations

```bash
ticktick tasks batch-create --file tasks_create.json [--json]
ticktick tasks batch-update --file tasks_update.json [--json]
ticktick tasks batch-delete --file tasks_delete.json [--json]
ticktick tasks batch-done --file tasks_complete.json [--json]
ticktick tasks batch-move --file tasks_move.json [--json]
ticktick tasks batch-parent --file tasks_parent.json [--json]
ticktick tasks batch-unparent --file tasks_unparent.json [--json]
ticktick tasks batch-pin --file tasks_pin.json [--json]
```

Batch payload formats:

`batch-create`:

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

`batch-update`:

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

`batch-delete` and `batch-done` (either format accepted):

```json
[
  ["TASK_ID", "PROJECT_ID"],
  { "task_id": "TASK_ID_2", "project_id": "PROJECT_ID_2" }
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

### Projects

```bash
ticktick projects list [--json]
ticktick projects get PROJECT_ID [--json]
ticktick projects data PROJECT_ID [--json]

ticktick projects create NAME \
  [--color #F18181] \
  [--kind TASK|NOTE] \
  [--view list|kanban|timeline] \
  [--folder FOLDER_ID] \
  [--json]

ticktick projects update PROJECT_ID \
  [--name NEW_NAME] \
  [--color #57A8FF] \
  [--folder FOLDER_ID | --remove-folder] \
  [--json]

ticktick projects delete PROJECT_ID [--json]
```

### Folders

```bash
ticktick folders list [--json]
ticktick folders create NAME [--json]
ticktick folders rename FOLDER_ID NAME [--json]
ticktick folders delete FOLDER_ID [--json]
```

### Columns

```bash
ticktick columns list --project PROJECT_ID [--json]
ticktick columns create --project PROJECT_ID NAME [--sort N] [--json]
ticktick columns update COLUMN_ID --project PROJECT_ID [--name NAME] [--sort N] [--json]
ticktick columns delete COLUMN_ID --project PROJECT_ID [--json]
```

### Tags

```bash
ticktick tags list [--json]
ticktick tags create NAME [--color #57A8FF] [--parent PARENT_TAG] [--json]
ticktick tags update NAME [--color #F18181] [--parent PARENT_TAG | --clear-parent] [--json]
ticktick tags rename OLD_NAME NEW_NAME [--json]
ticktick tags merge SOURCE TARGET [--json]
ticktick tags delete NAME [--json]
```

### Habits

```bash
ticktick habits list [--json]
ticktick habits get HABIT_ID [--json]
ticktick habits sections [--json]
ticktick habits preferences [--json]

ticktick habits create NAME \
  [--type Boolean|Real] \
  [--goal 1.0] \
  [--step 0.0] \
  [--unit Count] \
  [--icon habit_daily_check_in] \
  [--color #97E38B] \
  [--section SECTION_ID] \
  [--repeat RRULE] \
  [--reminders HH:MM,HH:MM] \
  [--target-days N] \
  [--encouragement TEXT] \
  [--json]

ticktick habits update HABIT_ID \
  [--name TEXT] \
  [--goal FLOAT] \
  [--step FLOAT] \
  [--unit TEXT] \
  [--icon TEXT] \
  [--color HEX] \
  [--section SECTION_ID] \
  [--repeat RRULE] \
  [--reminders HH:MM,HH:MM] \
  [--target-days N] \
  [--encouragement TEXT] \
  [--json]

ticktick habits delete HABIT_ID [--json]

ticktick habits checkin HABIT_ID [--value FLOAT] [--date YYYY-MM-DD] [--json]
ticktick habits batch-checkin --file checkins.json [--json]
ticktick habits checkins HABIT_ID [HABIT_ID ...] [--after-stamp YYYYMMDD] [--json]

ticktick habits archive HABIT_ID [--json]
ticktick habits unarchive HABIT_ID [--json]
```

`batch-checkin` file format:

```json
[
  {
    "habit_id": "HABIT_ID",
    "value": 1.0,
    "checkin_date": "2026-02-01"
  }
]
```

### User

```bash
ticktick user profile [--json]
ticktick user status [--json]
ticktick user statistics [--json]
ticktick user preferences [--json]
```

### Focus

```bash
ticktick focus heatmap [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--days N] [--json]
ticktick focus by-tag [--from YYYY-MM-DD] [--to YYYY-MM-DD] [--days N] [--json]
```

## Command Behavior Notes

### Project Resolution

When a task command needs project context and `--project` is omitted:

1. For existing-task operations (`done`, `abandon`, `delete`, `pin`, `unpin`,
   `column`, `update`, `subtask`, `unparent`), project is auto-resolved from
   the task.
2. For create/list-style operations, project is resolved in this order:
   - explicit `--project`
   - `TICKTICK_CURRENT_PROJECT_ID`
   - account inbox project ID

### Date and Timezone

- `--due` and `--start` accept `YYYY-MM-DD` or ISO datetime.
- `--from` and `--to` for focus commands use `YYYY-MM-DD`.
- `TZ` environment variable controls local date interpretation.
- `--time-zone` on task create/update can override stored timezone.

Example:

```bash
export TZ=America/New_York
ticktick tasks list --due 2026-02-09
```

## Environment Variables

Required:

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

## Troubleshooting

- `Error: missing credentials`:
  Check `.env` contains all required variables.
- OAuth flow issues:
  Confirm your app redirect URI exactly matches `TICKTICK_REDIRECT_URI`.
- Headless machine:
  Use `ticktick auth --manual`.
- Unexpected API host behavior:
  Set `TICKTICK_HOST=ticktick.com` or `TICKTICK_HOST=dida365.com` explicitly.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
.venv/bin/pytest -q
```

Live E2E suite (real TickTick test account via `.env.test`):

```bash
cp .env.example .env.test
```

Fill `.env.test` with your dedicated test account credentials. The E2E harness
loads `.env.test` automatically and keeps regular `.env` usage separate for
local/manual CLI work.

```bash
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e
```

Run a single functional area:

```bash
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e_tasks
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e_projects
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e_tags
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e_habits
```

## Build

```bash
python3 -m pip install build
python3 -m build
```

## PyPI Release

1. Bump version in `pyproject.toml`.
2. Run release checks and build artifacts:

```bash
.venv/bin/pytest -q tests/test_cli.py
python3 -m build
.venv/bin/twine check dist/*
```

3. (Optional) Upload to TestPyPI:

```bash
TWINE_USERNAME=__token__ \
TWINE_PASSWORD=<testpypi-token> \
.venv/bin/twine upload --repository testpypi dist/*
```

4. Upload to PyPI:

```bash
TWINE_USERNAME=__token__ \
TWINE_PASSWORD=<pypi-token> \
.venv/bin/twine upload dist/*
```

## Acknowledgments

- [TickTick](https://www.ticktick.com/) for providing the task platform and
  developer APIs used by this CLI.
- [`ticktick-sdk`](https://github.com/dev-mirzabicer/ticktick-sdk) for the API
  integration, authentication flows, MCP server implementation, and core data
  model/client foundation that powers `ticktick-cli`.

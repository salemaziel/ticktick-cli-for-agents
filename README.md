# ticktick-cli

A standalone command-line interface for TickTick.

`ticktick-cli` gives you scriptable access to tasks, projects, folders, columns, tags, habits, account data, focus analytics, and full sync payloads.

## Table of Contents

- [Agent Skill](#agent-skill)
- [Installation](#installation)
- [Authentication (Required)](#authentication-required)
- [Quick Start](#quick-start)
- [Global Usage](#global-usage)
- [Command Reference](#command-reference)
- [Behavior Notes](#behavior-notes)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Release Process](#release-process)
- [Acknowledgments](#acknowledgments)

## Agent Skill

Enable your AI agent (Gemini, Claude, Cursor) to manage your TickTick tasks, projects, and habits using natural language:

```bash
npx skills add https://github.com/salemaziel/ticktick-cli-for-agents --skill ticktick-cli
```

## Installation

Python 3.11+ is required.

Install from PyPI:

```bash
python3 -m pip install --upgrade ticktick-cli
```

If you are developing from this repository:

```bash
python3 -m pip install -e .
```

## Authentication (Required)

The CLI needs both authentication layers:

- OAuth app credentials for TickTick API access
- TickTick account credentials for session-based endpoints

### 1. Create a TickTick developer app

1. Open: <https://developer.ticktick.com/manage>
2. Create an app.
3. Set a Redirect URI (recommended):
   - `http://127.0.0.1:8080/callback`

Important: the Redirect URI in TickTick Developer Portal must exactly match `TICKTICK_REDIRECT_URI` in your environment.

### 2. Create `.env`

From your project/work directory:

```bash
cp .env.example .env
```

Set required values:

```dotenv
# OAuth app credentials
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
TICKTICK_REDIRECT_URI=http://127.0.0.1:8080/callback
TICKTICK_ACCESS_TOKEN=

# TickTick account credentials
TICKTICK_USERNAME=you@example.com
TICKTICK_PASSWORD=your_password
```

### 3. Run OAuth flow to obtain `TICKTICK_ACCESS_TOKEN`

Local desktop flow (opens browser):

```bash
ticktick auth
```

Headless / SSH flow:

```bash
ticktick auth --manual
```

After success, copy the printed access token into:

```dotenv
TICKTICK_ACCESS_TOKEN=...
```

### 4. Verify auth and connectivity

Run a read command:

```bash
ticktick projects list --json
```

If this command returns data, your environment is configured correctly.

## Quick Start

```bash
# List projects
ticktick projects list

# Add task (project auto-resolves if --project is omitted)
ticktick tasks add "Buy coffee" --priority medium --due 2026-02-12

# Complete task
ticktick tasks done TASK_ID

# Show full account sync payload
ticktick sync --json
```

## Global Usage

```bash
ticktick --help
ticktick --version
ticktick --json <command>
```

Notes:

- `--json` is supported on data commands and is recommended for scripting.
- `auth` accepts `--json` for CLI consistency, but output remains text/interactive.
- Running `ticktick` without a command prints help.

## Command Reference

### Auth

```bash
ticktick auth
ticktick auth --manual
```

### Sync

```bash
ticktick sync --json
```

Returns the raw full-account sync payload.

### Tasks

Read/query:

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

Create:

```bash
ticktick tasks add TITLE \
  [--project PROJECT_ID] \
  [--content TEXT] \
  [--description TEXT] \
  [--kind TEXT|NOTE|CHECKLIST] \
  [--start YYYY-MM-DD|ISO_DATETIME|NATURAL] \
  [--due YYYY-MM-DD|ISO_DATETIME|NATURAL] \
  [--priority none|low|medium|high] \
  [--tags tag1,tag2] \
  [--recurrence RRULE] \
  [--time-zone IANA_TZ] \
  [--all-day|--timed] \
  [--parent PARENT_TASK_ID] \
  [--reminders TRIGGER_1,TRIGGER_2] \
  [--json]

# Quick parser-style create
ticktick tasks quick-add TEXT [--project PROJECT_ID] [--json]
```

Update/lifecycle:

```bash
ticktick tasks update TASK_ID \
  [--project PROJECT_ID] \
  [--title TEXT] \
  [--content TEXT] \
  [--description TEXT] \
  [--kind TEXT|NOTE|CHECKLIST] \
  [--priority none|low|medium|high] \
  [--start YYYY-MM-DD|ISO_DATETIME|NATURAL|--clear-start] \
  [--due YYYY-MM-DD|ISO_DATETIME|NATURAL|--clear-due] \
  [--tags tag1,tag2|--clear-tags] \
  [--recurrence RRULE|--clear-recurrence] \
  [--time-zone IANA_TZ] \
  [--all-day|--timed] \
  [--json]

ticktick tasks done TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks abandon TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks delete TASK_ID [--project PROJECT_ID] [--json]
```

Task relationships/moves:

```bash
ticktick tasks move TASK_ID --to-project PROJECT_ID [--from-project PROJECT_ID] [--json]
ticktick tasks subtask TASK_ID --parent PARENT_TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks unparent TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks pin TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks unpin TASK_ID [--project PROJECT_ID] [--json]
ticktick tasks column TASK_ID [--project PROJECT_ID] (--column COLUMN_ID | --clear-column) [--json]
```

Priority accepts `none|low|medium|high` and numeric forms `0|1|3|5` where relevant.

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
  [--goal FLOAT] \
  [--step FLOAT] \
  [--unit TEXT] \
  [--icon ICON_KEY] \
  [--color HEX] \
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
  [--icon ICON_KEY] \
  [--color HEX] \
  [--section SECTION_ID] \
  [--repeat RRULE] \
  [--reminders HH:MM,HH:MM] \
  [--target-days N] \
  [--encouragement TEXT] \
  [--json]

ticktick habits checkin HABIT_ID [--value FLOAT] [--date YYYY-MM-DD] [--json]
ticktick habits archive HABIT_ID [--json]
ticktick habits unarchive HABIT_ID [--json]
ticktick habits delete HABIT_ID [--json]
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

## Behavior Notes

### Project resolution

When `--project` is omitted:

- Existing-task mutation operations (`update`, `done`, `abandon`, `delete`, `pin`, `unpin`, `column`, `subtask`, `unparent`) resolve project from the target task.
- Create-style operations (`add`, `quick-add`) resolve in this order:
  1. explicit `--project`
  2. `TICKTICK_CURRENT_PROJECT_ID`
  3. inbox project ID
- Query operations (`list`, `search`, `by-tag`, `by-priority`, `today`, `overdue`, `completed`, `abandoned`, `deleted`) default to all projects.

### Date, time, timezone

- `tasks --due` filter expects `YYYY-MM-DD`.
- `tasks add/update --start` and `--due` accept `YYYY-MM-DD`, ISO datetime, or natural language expressions (e.g. `today`, `tomorrow`, `next monday`, `in 3 days`, `in 2 weeks`).
- `focus --from/--to` and `habits checkin --date` expect `YYYY-MM-DD`.
- `TZ` controls local date interpretation in CLI output/filtering.
- `--time-zone` on task create/update sets stored task timezone explicitly.

### Host selection

Set region host explicitly when needed:

```bash
export TICKTICK_HOST=ticktick.com
# or
export TICKTICK_HOST=dida365.com
```

## Environment Variables

Required:

- `TICKTICK_CLIENT_ID`
- `TICKTICK_CLIENT_SECRET`
- `TICKTICK_ACCESS_TOKEN`
- `TICKTICK_USERNAME`
- `TICKTICK_PASSWORD`

Common optional:

- `TICKTICK_REDIRECT_URI` (default auth callback URI)
- `TICKTICK_HOST` (`ticktick.com` or `dida365.com`)
- `TICKTICK_CURRENT_PROJECT_ID` (default project for task creation)
- `TZ` (timezone for local date behavior)
- `TICKTICK_TIMEOUT`
- `TICKTICK_DEVICE_ID`

## Troubleshooting

### "Configuration error" or missing env vars

- Ensure all required variables are present in `.env` or exported in shell.
- Re-run:

```bash
ticktick projects list --json
```

### OAuth redirect mismatch

- Ensure `TICKTICK_REDIRECT_URI` matches your app redirect URI exactly.
- Re-run `ticktick auth` (or `ticktick auth --manual`).

### `ticktick: command not found`

- Install/upgrade:

```bash
python3 -m pip install --upgrade ticktick-cli
```

- If PATH still does not expose the script, run via module:

```bash
python3 -m ticktick_cli --help
```

- For local source checkout without package install:

```bash
PYTHONPATH=src python3 -m ticktick_cli --help
```

### Wrong region behavior

- Set `TICKTICK_HOST` explicitly (`ticktick.com` or `dida365.com`).

### Date output/filter looks wrong

- Set `TZ` to the desired IANA timezone (for example `America/New_York`).
- Prefer explicit ISO datetime for timed tasks.

## Development

Create local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,release]"
```

Run unit tests:

```bash
.venv/bin/pytest -q
```

Run live E2E tests (requires real test account credentials in `.env.test`):

```bash
TICKTICK_RUN_E2E=1 .venv/bin/pytest -q tests/e2e -m e2e
```

Build distribution:

```bash
python3 -m build
```

## Release Process

Use the standard Python release flow documented in `RELEASING.md`.

Minimal prepare commands:

```bash
make release-check
```

## Acknowledgments

- [TickTick](https://www.ticktick.com/) for the platform and developer APIs.
- [`ticktick-sdk`](https://github.com/dev-mirzabicer/ticktick-sdk) for the underlying API/auth client infrastructure powering this CLI.

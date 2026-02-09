# TickTick CLI Command Recipes

Use this file when you need exact commands or payload shapes while operating the local `ticktick` CLI.

## Preflight

```bash
ticktick --version
ticktick projects list --json
```

If auth is required:

```bash
ticktick auth
# or
ticktick auth --manual
```

## Core Read Patterns

```bash
# Tasks
ticktick tasks list --json
ticktick tasks get TASK_ID --project PROJECT_ID --json
ticktick tasks search "invoice" --project PROJECT_ID --json
ticktick tasks today --json
ticktick tasks overdue --json

# Structure and taxonomy
ticktick projects list --json
ticktick folders list --json
ticktick columns list --project PROJECT_ID --json
ticktick tags list --json

# Habits, user, focus
ticktick habits list --json
ticktick user profile --json
ticktick focus heatmap --days 30 --json
ticktick focus by-tag --days 30 --json

# Full raw sync payload
ticktick sync --json
```

## Task Mutation Recipes

```bash
# Create
ticktick tasks add "Buy coffee" \
  --project PROJECT_ID \
  --priority medium \
  --due 2026-02-15 \
  --tags errands,home \
  --json

# Update
ticktick tasks update TASK_ID \
  --project PROJECT_ID \
  --title "Buy coffee beans" \
  --priority high \
  --json

# Complete / delete / move
ticktick tasks done TASK_ID --project PROJECT_ID --json
ticktick tasks delete TASK_ID --project PROJECT_ID --json
ticktick tasks move TASK_ID --to-project TARGET_PROJECT_ID --from-project SOURCE_PROJECT_ID --json

# Hierarchy and pinning
ticktick tasks subtask TASK_ID --parent PARENT_TASK_ID --project PROJECT_ID --json
ticktick tasks unparent TASK_ID --project PROJECT_ID --json
ticktick tasks pin TASK_ID --project PROJECT_ID --json
ticktick tasks unpin TASK_ID --project PROJECT_ID --json
```

## Project and Organization Recipes

```bash
# Projects
ticktick projects create "Launch Plan" --view kanban --json
ticktick projects update PROJECT_ID --name "Launch Plan Q2" --json
ticktick projects delete PROJECT_ID --json

# Folders
ticktick folders create "Work" --json
ticktick folders rename FOLDER_ID "Client Work" --json
ticktick folders delete FOLDER_ID --json

# Columns
ticktick columns create --project PROJECT_ID "In Review" --sort 20 --json
ticktick columns update COLUMN_ID --project PROJECT_ID --name "Ready" --json
ticktick columns delete COLUMN_ID --project PROJECT_ID --json

# Tags
ticktick tags create "urgent" --color '#F18181' --json
ticktick tags rename urgent asap --json
ticktick tags merge old-tag new-tag --json
ticktick tags delete asap --json
```

## Habit Recipes

```bash
ticktick habits create "Drink Water" --goal 8 --unit cups --type Real --json
ticktick habits update HABIT_ID --goal 10 --json
ticktick habits checkin HABIT_ID --value 8 --date 2026-02-09 --json
ticktick habits checkins HABIT_ID --json
ticktick habits delete HABIT_ID --json
```

## Batch Payload Skeletons

`tasks_create.json`:

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

`tasks_update.json`:

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

`tasks_delete.json` and `tasks_done.json`:

```json
[
  ["TASK_ID", "PROJECT_ID"],
  { "task_id": "TASK_ID_2", "project_id": "PROJECT_ID_2" }
]
```

`tasks_move.json`:

```json
[
  {
    "task_id": "TASK_ID",
    "from_project_id": "FROM_PROJECT_ID",
    "to_project_id": "TO_PROJECT_ID"
  }
]
```

`tasks_parent.json`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID",
    "parent_id": "PARENT_TASK_ID"
  }
]
```

`tasks_unparent.json`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID"
  }
]
```

`tasks_pin.json`:

```json
[
  {
    "task_id": "TASK_ID",
    "project_id": "PROJECT_ID",
    "pin": true
  }
]
```

`habit_checkins.json`:

```json
[
  {
    "habit_id": "HABIT_ID",
    "value": 1.0,
    "checkin_date": "2026-02-01"
  }
]
```

Run batch commands:

```bash
ticktick tasks batch-create --file tasks_create.json --json
ticktick tasks batch-update --file tasks_update.json --json
ticktick tasks batch-delete --file tasks_delete.json --json
ticktick tasks batch-done --file tasks_done.json --json
ticktick tasks batch-move --file tasks_move.json --json
ticktick tasks batch-parent --file tasks_parent.json --json
ticktick tasks batch-unparent --file tasks_unparent.json --json
ticktick tasks batch-pin --file tasks_pin.json --json
ticktick habits batch-checkin --file habit_checkins.json --json
```

## Resolution Rules

- Existing task operations can auto-resolve project context if `--project` is omitted.
- Create/list task operations resolve project in this order:
  1. explicit `--project`
  2. `TICKTICK_CURRENT_PROJECT_ID`
  3. account inbox project ID

Use explicit `--project` when deterministic behavior is required.

## Troubleshooting

- Missing credentials error: verify required environment variables and rerun auth.
- OAuth callback mismatch: ensure app redirect URI matches `TICKTICK_REDIRECT_URI`.
- Headless environment: use `ticktick auth --manual`.
- Unexpected region behavior: set `TICKTICK_HOST` explicitly to `ticktick.com` or `dida365.com`.

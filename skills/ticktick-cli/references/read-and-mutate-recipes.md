# TickTick CLI Read and Mutate Recipes

## Contents

- Command family map
- Read patterns
- Mutation patterns
- Project resolution rules
- Date and timezone rules

## Command family map

- `tasks`: lifecycle, filtering, search, pinning, move, hierarchy
- `projects`: create/update/delete project containers
- `folders`: top-level project grouping
- `columns`: kanban column management
- `tags`: taxonomy create/update/merge/delete
- `habits`: habit lifecycle and check-ins
- `user`: profile, status, statistics, preferences
- `focus`: focus analytics
- `sync`: full raw account payload

## Read patterns

```bash
# Tasks
ticktick tasks list --json
ticktick tasks get TASK_ID --project PROJECT_ID --json
ticktick tasks search "invoice" --project PROJECT_ID --json
ticktick tasks by-tag TAG_NAME --project PROJECT_ID --json
ticktick tasks by-priority high --project PROJECT_ID --json
ticktick tasks today --json
ticktick tasks overdue --json
ticktick tasks completed --days 30 --limit 50 --json
ticktick tasks deleted --limit 50 --json

# Structure
ticktick projects list --json
ticktick projects get PROJECT_ID --json
ticktick projects data PROJECT_ID --json
ticktick folders list --json
ticktick columns list --project PROJECT_ID --json
ticktick tags list --json

# Habits and analytics
ticktick habits list --json
ticktick habits get HABIT_ID --json
ticktick user profile --json
ticktick user status --json
ticktick user statistics --json
ticktick focus heatmap --days 30 --json
ticktick focus by-tag --days 30 --json

# Full account payload
ticktick sync --json
```

## Mutation patterns

```bash
# Create task
ticktick tasks add "Buy coffee" \
  --project PROJECT_ID \
  --priority medium \
  --due YYYY-MM-DD \
  --tags errands,home \
  --json

# Update task
ticktick tasks update TASK_ID \
  --project PROJECT_ID \
  --title "Buy coffee beans" \
  --priority high \
  --json

# Complete / delete / move task
ticktick tasks done TASK_ID --project PROJECT_ID --json
ticktick tasks delete TASK_ID --project PROJECT_ID --json
ticktick tasks move TASK_ID --to-project TARGET_PROJECT_ID --from-project SOURCE_PROJECT_ID --json

# Hierarchy / pinning / columns
ticktick tasks subtask TASK_ID --parent PARENT_TASK_ID --project PROJECT_ID --json
ticktick tasks unparent TASK_ID --project PROJECT_ID --json
ticktick tasks pin TASK_ID --project PROJECT_ID --json
ticktick tasks unpin TASK_ID --project PROJECT_ID --json
ticktick tasks column TASK_ID --project PROJECT_ID --column COLUMN_ID --json
```

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
ticktick tags update urgent --color '#57A8FF' --json
ticktick tags rename urgent asap --json
ticktick tags merge old-tag new-tag --json
ticktick tags delete asap --json

# Habits
ticktick habits create "Drink Water" --goal 8 --unit cups --type Real --json
ticktick habits update HABIT_ID --goal 10 --json
ticktick habits checkin HABIT_ID --value 8 --date YYYY-MM-DD --json
ticktick habits archive HABIT_ID --json
ticktick habits unarchive HABIT_ID --json
ticktick habits delete HABIT_ID --json
```

## Project resolution rules

- Existing task lifecycle commands can auto-resolve project if `--project` is omitted.
- Create/list task commands resolve project in this order:
  1. explicit `--project`
  2. `TICKTICK_CURRENT_PROJECT_ID`
  3. account inbox project ID

Prefer explicit `--project` when deterministic behavior is required.

## Date and timezone rules

- Use `YYYY-MM-DD` for date-only fields.
- Use ISO datetimes for time-specific fields.
- Set `TZ` to control local date interpretation.
- Set `--time-zone` during task create/update when stored timezone must be explicit.

# ticktick-cli

Standalone command-line interface for TickTick, powered by
[`ticktick-sdk`](https://pypi.org/project/ticktick-sdk/).

This repository contains only CLI code and depends on `ticktick-sdk` for API
and auth implementation.

## Installation

```bash
pip install ticktick-cli
```

## Commands

```bash
ticktick --help
ticktick server
ticktick auth
ticktick auth --manual
ticktick tasks list
ticktick tasks add "Buy groceries" --due 2025-02-10 --priority high
ticktick tasks done TASK_ID
ticktick tasks abandon TASK_ID
ticktick projects list
```

## JSON Output

Task and project commands support `--json`:

```bash
ticktick tasks list --json
ticktick tasks add "Review PR" --json
ticktick projects list --json
```

## Project Resolution

When `--project` is omitted for task commands, project ID is resolved in order:

1. `--project PROJECT_ID`
2. `TICKTICK_CURRENT_PROJECT_ID`
3. inbox project ID from account status

## Timezone

Set `TZ` to an IANA timezone to ensure correct due-date parsing/filtering:

```bash
export TZ=America/New_York
ticktick tasks list --due 2025-02-09
```

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

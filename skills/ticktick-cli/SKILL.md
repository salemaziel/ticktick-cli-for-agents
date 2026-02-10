---
name: ticktick-cli
description: Operate TickTick through the `ticktick` command-line interface, including authentication, read/query flows, and safe mutations for tasks, projects, folders, columns, tags, habits, user info, focus analytics, and sync payloads. Use when users ask to run TickTick terminal commands, parse TickTick CLI JSON output, resolve IDs, or fix TickTick CLI configuration/auth failures.
---

# TickTick CLI

Use this skill to execute TickTick workflows directly from terminal commands with deterministic output handling.

## Execution Policy

1. Execute the requested `ticktick ...` command first. Do not run version or tool-presence pre-checks.
2. If execution fails because CLI is missing, install and retry:
   - `python3 -m pip install --upgrade ticktick-cli`
   - Retry the same command.
3. If the `ticktick` entrypoint is still unavailable in a local-source context, retry with module form:
   - `PYTHONPATH=src python3 -m ticktick_cli ...`
4. Use `--help` only as recovery when a command fails due unknown flags/arguments or missing required params.

## Defaults

- Prefer `--json` on all data commands and parse structured output.
- Resolve names to IDs before mutations; never guess identifiers.
- Prefer explicit `--project PROJECT_ID` for task mutations when deterministic behavior matters.
- Use explicit date formats:
  - `YYYY-MM-DD` for date-only fields
  - ISO datetime for timed fields
- Apply read -> mutate -> verify for every write operation.
- Avoid batch commands unless user explicitly requests batch behavior.

## Mutation Checklist

```text
Mutation Progress:
- [ ] Confirm user intent for mutation
- [ ] Read current state
- [ ] Resolve IDs
- [ ] Execute narrowest mutation command
- [ ] Re-read and verify
- [ ] Report changed fields and IDs
```

## Safety

- Require explicit user confirmation before destructive operations:
  - `tasks delete`
  - `projects delete`
  - `folders delete`
  - `columns delete`
  - `tags delete`
  - `tags merge`
  - `habits delete`
- Redact secrets/tokens from user-visible output.

## Reference Map

Load only the file needed for the active area.

- Setup and auth: `references/setup-and-auth.md`
- Tasks: `references/tasks.md`
- Projects: `references/projects.md`
- Folders: `references/folders.md`
- Columns: `references/columns.md`
- Tags: `references/tags.md`
- Habits: `references/habits.md`
- User, focus, sync: `references/user-focus-sync.md`
- Troubleshooting: `references/troubleshooting.md`

Use `references/read-and-mutate-recipes.md` only as a lightweight navigation index.

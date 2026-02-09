---
name: ticktick-cli
description: Operate the local ticktick-cli command-line tool to authenticate with TickTick and run read/write workflows for tasks, projects, folders, columns, tags, habits, user profile data, focus analytics, and full sync payloads. Use when users ask to manage TickTick from terminal commands, need JSON command output, must resolve project/task IDs, run batch operations from JSON files, or troubleshoot TickTick CLI credentials and environment variables.
---

# TickTick CLI

## Overview

Use this skill to execute TickTick operations through the local `ticktick` binary. Prefer JSON-first execution, resolve IDs before mutations, and verify authentication before any write operation.

## Run Preflight Checks

1. Confirm CLI availability with `ticktick --version`.
2. Confirm required credentials exist in environment or `.env`:
`TICKTICK_CLIENT_ID`, `TICKTICK_CLIENT_SECRET`, `TICKTICK_ACCESS_TOKEN`, `TICKTICK_USERNAME`, `TICKTICK_PASSWORD`.
3. Run `ticktick auth` when token is missing or expired. Use `ticktick auth --manual` in headless environments.
4. Confirm account connectivity with `ticktick projects list --json` before mutating data.

## Apply Execution Defaults

- Add `--json` on data commands and parse structured output instead of human text.
- Resolve names to IDs before write operations:
  - projects: `ticktick projects list --json`
  - folders: `ticktick folders list --json`
  - columns: `ticktick columns list --project PROJECT_ID --json`
  - habits: `ticktick habits list --json`
- Prefer explicit `--project PROJECT_ID` for deterministic task writes, even though auto-resolution exists for many task lifecycle commands.
- Use explicit date input:
  - `YYYY-MM-DD` for date-only fields
  - ISO datetime when time precision is required
- Set `TZ` when local date interpretation matters.
- Set `TICKTICK_HOST` explicitly when routing should be pinned to `ticktick.com` or `dida365.com`.

## Choose the Correct Command Family

- Use `tasks` for task lifecycle, filtering/search, pinning, column moves, parenting, and batch actions.
- Use `projects`, `folders`, and `columns` for structural organization.
- Use `tags` for taxonomy operations.
- Use `habits` for habit lifecycle and check-ins.
- Use `user` for profile/status/statistics/preferences reads.
- Use `focus` for focus analytics.
- Use `sync` for raw account payload inspection.
- Use `server` only when intentionally launching tool-server mode.

## Execute Mutations Safely

1. Read current state (`list` or `get`).
2. Resolve IDs from current output.
3. Execute the narrowest mutation command.
4. Re-read the entity to confirm the result.
5. Prefer `batch-*` commands with validated JSON files for bulk updates.

## Load References Only When Needed

- Read `references/command-recipes.md` when exact command syntax, payload examples, or troubleshooting snippets are needed.
- Keep normal execution in this file and load references only for details.

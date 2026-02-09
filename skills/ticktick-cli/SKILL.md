---
name: ticktick-cli
description: Operates TickTick through the ticktick-cli command-line interface, including installation/bootstrap, authentication, and deterministic read/write workflows for tasks, projects, folders, columns, tags, habits, user profile data, focus analytics, and full sync payload inspection. Use when users request TickTick terminal command execution, JSON output parsing, ID resolution, or troubleshooting TickTick CLI credentials and environment configuration.
---

# TickTick CLI

## Overview

Use this skill to run TickTick operations through CLI commands with reliable preflight checks, explicit ID resolution, and post-mutation verification.

## Choose a Workflow

- Use the setup workflow for installation, environment configuration, and OAuth bootstrap.
- Use the read workflow for list, search, analytics, and sync inspection requests.
- Use the mutation workflow for create, update, move, complete, delete, or rename requests.
- Use troubleshooting workflow when credentials, OAuth redirect, region host, or command semantics fail.

## Run Preflight Checks

1. Confirm CLI availability with `ticktick --version`.
2. If entrypoint is unavailable, use module fallback form `python3 -m ticktick_cli`.
3. Confirm required credentials exist in environment or `.env`:
   `TICKTICK_CLIENT_ID`, `TICKTICK_CLIENT_SECRET`, `TICKTICK_ACCESS_TOKEN`, `TICKTICK_USERNAME`, `TICKTICK_PASSWORD`.
4. Run OAuth when token is missing or expired (`ticktick auth` or `ticktick auth --manual`).
5. Confirm account connectivity with `ticktick projects list --json` before mutations.

## Apply Execution Defaults

- Prefer JSON-first execution:
  - add `--json` on data commands
  - parse machine output instead of text tables
- Resolve names to IDs before mutations; never guess identifiers.
- Prefer explicit `--project PROJECT_ID` for deterministic task writes.
- Use explicit date input:
  - `YYYY-MM-DD` for date-only values
  - ISO datetime for time-specific values
- Set `TZ` when local date interpretation matters.
- Set `TICKTICK_HOST` explicitly when routing should be pinned to `ticktick.com` or `dida365.com`.
- Treat `auth` and `server` output as text-oriented even if `--json` is passed.

## Enforce Safety Rules

- Require explicit user intent before destructive operations:
  - delete operations (`tasks delete`, `projects delete`, `folders delete`, `columns delete`, `tags delete`)
  - tag merges
- Redact credentials and tokens from user-visible output.
- For every mutation, perform read -> mutate -> verify loop.

## Run the Read Workflow

1. Identify the command family (`tasks`, `projects`, `folders`, `columns`, `tags`, `habits`, `user`, `focus`, `sync`).
2. Resolve optional scope first (project, folder, tag, date range).
3. Execute a read command with `--json`.
4. Return only the requested fields or summary.

## Run the Mutation Workflow

Copy and track this checklist:

```text
Mutation Progress:
- [ ] Step 1: Confirm explicit user intent for mutation
- [ ] Step 2: Read current state (`list` or `get`)
- [ ] Step 3: Resolve required IDs from current data
- [ ] Step 4: Execute the narrowest mutation command
- [ ] Step 5: Re-read entity and verify result
- [ ] Step 6: Report changed fields and IDs
```

## Run the Setup Workflow

1. Follow `references/setup-and-auth.md`.
2. Install package only when missing or when local editable install is requested.
3. Configure `.env` and run OAuth bootstrap.
4. Validate installation with version and a JSON read command.

## Run the Troubleshooting Workflow

1. Identify failure class (credentials, OAuth redirect mismatch, region host, missing project context, date/time parsing).
2. Follow targeted fixes in `references/troubleshooting.md`.
3. Re-run minimal verification command after each fix.

## Load References On Demand

- Setup and OAuth: `references/setup-and-auth.md`
- Single-entity reads and writes: `references/read-and-mutate-recipes.md`
- Troubleshooting patterns: `references/troubleshooting.md`

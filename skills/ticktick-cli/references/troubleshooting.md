# TickTick CLI Troubleshooting

## Contents

- Missing credentials
- OAuth problems
- Command not found
- Wrong region host
- Project resolution surprises
- Date and timezone confusion

## Missing credentials

Symptoms:

- Error mentions missing credentials
- Authenticated commands fail immediately

Fix:

1. Verify required values exist:
`TICKTICK_CLIENT_ID`, `TICKTICK_CLIENT_SECRET`, `TICKTICK_ACCESS_TOKEN`, `TICKTICK_USERNAME`, `TICKTICK_PASSWORD`.
2. Re-run auth if token is absent or expired:
   - `ticktick auth`
   - `ticktick auth --manual` for headless sessions.
3. Re-test with:
   - `ticktick projects list --json`

## OAuth problems

Symptoms:

- OAuth callback fails
- Redirect mismatch error

Fix:

1. Confirm redirect URI in TickTick developer app matches `TICKTICK_REDIRECT_URI` exactly.
2. Re-run auth flow.
3. Persist returned access token.

## Command not found

Symptoms:

- `ticktick: command not found`

Fix:

1. Install package:
   - `python3 -m pip install --upgrade ticktick-cli`
2. If entrypoint still unavailable, use module fallback:
   - `python3 -m ticktick_cli --version`
   - `python3 -m ticktick_cli projects list --json`

## Wrong region host

Symptoms:

- Unexpected host behavior
- Account routed to incorrect region

Fix:

Set host explicitly:

```bash
export TICKTICK_HOST=ticktick.com
# or
export TICKTICK_HOST=dida365.com
```

## Project resolution surprises

Symptoms:

- Mutation affects unexpected project
- Create/list commands default to inbox unexpectedly

Fix:

1. Pass explicit `--project PROJECT_ID`.
2. If using implicit behavior intentionally, verify `TICKTICK_CURRENT_PROJECT_ID`.
3. Re-check with `ticktick tasks list --project PROJECT_ID --json`.

## Date and timezone confusion

Symptoms:

- Tasks show unexpected due date or time

Fix:

1. Use explicit `YYYY-MM-DD` or ISO datetime inputs.
2. Set `TZ` before date-sensitive commands.
3. Use `--time-zone` on task create/update when needed.

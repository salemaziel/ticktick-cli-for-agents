# TickTick CLI Troubleshooting

## Contents

- Missing CLI executable
- Missing credentials
- OAuth redirect/auth issues
- Parameter mismatch errors
- Host routing issues
- Project resolution surprises
- Date/time confusion

## Missing CLI executable

Symptoms:

- `ticktick: command not found`
- Entry-point not available

Fix:

1. Install (or upgrade) only after failure:

```bash
python3 -m pip install --upgrade ticktick-cli
```

2. Retry original command.
3. If script entrypoint remains unavailable in source checkout, use module fallback:

```bash
PYTHONPATH=src python3 -m ticktick_cli <same-args>
```

## Missing credentials

Symptoms:

- `Configuration error: ...`
- Output mentions missing env vars

Fix:

1. Ensure required values exist:
   - `TICKTICK_CLIENT_ID`
   - `TICKTICK_CLIENT_SECRET`
   - `TICKTICK_ACCESS_TOKEN`
   - `TICKTICK_USERNAME`
   - `TICKTICK_PASSWORD`
2. Re-run auth if token missing/expired:
   - `ticktick auth`
   - `ticktick auth --manual`
3. Verify with:
   - `ticktick projects list --json`

## OAuth redirect/auth issues

Symptoms:

- OAuth callback fails
- Redirect mismatch
- No code/token returned

Fix:

1. Confirm app redirect URI in TickTick Developer Portal exactly matches `TICKTICK_REDIRECT_URI`.
2. Re-run OAuth command.
3. Save returned token into `TICKTICK_ACCESS_TOKEN`.

## Parameter mismatch errors

Symptoms:

- argparse errors (`unrecognized arguments`, `required`, invalid value)
- validation errors from command handler

Fix:

1. Open only the relevant domain reference file and validate args.
2. If still unclear, use help as recovery:

```bash
ticktick <group> <action> --help
```

Do not use `--help` as a default pre-step when parameters are already known.

## Host routing issues

Symptoms:

- Wrong region behavior
- Unexpected auth/session behavior

Fix:

```bash
export TICKTICK_HOST=ticktick.com
# or
export TICKTICK_HOST=dida365.com
```

## Project resolution surprises

Symptoms:

- Task created or mutated in unexpected project

Fix:

1. Pass explicit `--project PROJECT_ID` on task commands.
2. Check `TICKTICK_CURRENT_PROJECT_ID` when relying on implicit create behavior.
3. Re-verify with scoped read command:

```bash
ticktick tasks list --project PROJECT_ID --json
```

## Date/time confusion

Symptoms:

- Due dates appear shifted
- `--due` filters return unexpected results

Fix:

1. Use explicit `YYYY-MM-DD` or ISO datetime inputs.
2. Set `TZ` to intended timezone.
3. Set task `--time-zone` when stored timezone must be explicit.

# TickTick CLI Setup and Auth

## Contents

- Install strategy
- Required credentials
- Environment setup
- OAuth flow
- Connectivity verification

## Install strategy

Run the target `ticktick ...` command first.

Install only when command execution fails with missing CLI errors (`command not found`, `No module named ticktick_cli`, missing entrypoint):

```bash
python3 -m pip install --upgrade ticktick-cli
```

Retry the original command after installation.

If the script entrypoint is still unavailable in a local-source checkout, use:

```bash
PYTHONPATH=src python3 -m ticktick_cli <same-args>
```

## Required credentials

TickTick CLI needs all of these values for full functionality:

```dotenv
TICKTICK_CLIENT_ID=
TICKTICK_CLIENT_SECRET=
TICKTICK_REDIRECT_URI=http://127.0.0.1:8080/callback
TICKTICK_ACCESS_TOKEN=
TICKTICK_USERNAME=
TICKTICK_PASSWORD=
```

Credential meaning:

- `TICKTICK_CLIENT_ID` / `TICKTICK_CLIENT_SECRET`: app credentials from TickTick Developer Portal.
- `TICKTICK_REDIRECT_URI`: OAuth callback URL; must exactly match app config.
- `TICKTICK_ACCESS_TOKEN`: OAuth token returned by `ticktick auth`.
- `TICKTICK_USERNAME` / `TICKTICK_PASSWORD`: account credentials for session endpoints.

## Environment setup

Create `.env` from template when available:

```bash
cp .env.example .env
```

Fill required values.

Optional but common:

```dotenv
TICKTICK_HOST=ticktick.com
TICKTICK_CURRENT_PROJECT_ID=
TZ=UTC
```

## OAuth flow

1. Create app at <https://developer.ticktick.com/manage>.
2. Set redirect URI in app config (commonly `http://127.0.0.1:8080/callback`).
3. Run auth command:

```bash
ticktick auth
```

For SSH/headless environments:

```bash
ticktick auth --manual
```

Manual mode behavior:

- CLI prints authorization URL.
- User opens URL in any browser.
- After approve, browser redirects to callback URL.
- User copies `code` query parameter and pastes into terminal.

4. Persist returned access token into `.env` as `TICKTICK_ACCESS_TOKEN`.

## Connectivity verification

Run minimal JSON read:

```bash
ticktick projects list --json
```

Successful JSON response means auth/config are usable.

If parameters are unclear after a command failure, use help as recovery:

```bash
ticktick <group> <action> --help
```

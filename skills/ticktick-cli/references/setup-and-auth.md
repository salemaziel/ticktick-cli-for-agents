# TickTick CLI Setup and Authentication

## Contents

- Prerequisites
- Install the CLI
- Choose command invocation
- Configure environment variables
- Run OAuth bootstrap
- Verify connectivity

## Prerequisites

- Python 3.11 or newer
- Internet access for TickTick APIs and OAuth callback flow
- TickTick developer app credentials and account credentials

## Install the CLI

Install from PyPI:

```bash
python3 -m pip install --upgrade ticktick-cli
```

If working from this repository and validating local source changes:

```bash
python3 -m pip install -e .
```

## Choose command invocation

Prefer direct entrypoint:

```bash
ticktick --version
```

If `ticktick` is not on PATH, use module fallback:

```bash
python3 -m ticktick_cli --version
```

For all subsequent commands, use the same invocation style consistently.

## Configure environment variables

Create `.env` from `.env.example` when available:

```bash
cp .env.example .env
```

Required values:

```dotenv
TICKTICK_CLIENT_ID=your_client_id
TICKTICK_CLIENT_SECRET=your_client_secret
TICKTICK_REDIRECT_URI=http://127.0.0.1:8080/callback
TICKTICK_ACCESS_TOKEN=
TICKTICK_USERNAME=you@example.com
TICKTICK_PASSWORD=your_password
```

Common optional values:

```dotenv
TICKTICK_HOST=ticktick.com
TICKTICK_TIMEOUT=30
TICKTICK_CURRENT_PROJECT_ID=
TZ=UTC
```

## Run OAuth bootstrap

Interactive local environment:

```bash
ticktick auth
```

Headless or SSH environment:

```bash
ticktick auth --manual
```

After auth succeeds, persist `TICKTICK_ACCESS_TOKEN`.

## Verify connectivity

Run a minimal JSON command:

```bash
ticktick projects list --json
```

If using module fallback:

```bash
python3 -m ticktick_cli projects list --json
```

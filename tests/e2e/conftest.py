"""Shared fixtures/helpers for live E2E CLI tests."""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable

import pytest
from dotenv import load_dotenv
from jsonschema import Draft202012Validator

ROOT_DIR = Path(__file__).resolve().parents[2]
REF_DIR = ROOT_DIR / "tests" / "e2e" / "references"
E2E_ENV_PATH = ROOT_DIR / ".env.test"

REQUIRED_ENV_VARS = [
    "TICKTICK_CLIENT_ID",
    "TICKTICK_CLIENT_SECRET",
    "TICKTICK_ACCESS_TOKEN",
    "TICKTICK_USERNAME",
    "TICKTICK_PASSWORD",
]


def _load_e2e_env(*, override: bool) -> None:
    """Load dedicated E2E credentials from .env.test when available."""
    if E2E_ENV_PATH.exists():
        load_dotenv(dotenv_path=E2E_ENV_PATH, override=override)


@dataclass
class LiveState:
    """Tracks created resources for best-effort cleanup."""

    prefix: str
    folder_ids: set[str] = field(default_factory=set)
    project_ids: set[str] = field(default_factory=set)
    tag_names: set[str] = field(default_factory=set)
    habit_ids: set[str] = field(default_factory=set)
    task_locations: dict[str, str] = field(default_factory=dict)


class CLIRunner:
    """Runs CLI commands in subprocesses and validates JSON payload schemas."""

    def __init__(self, schema_catalog: dict[str, Any]) -> None:
        self.schema_catalog = schema_catalog
        self.command_schemas = schema_catalog["command_schemas"]

    def run_text(self, args: list[str], *, expected_exit_code: int = 0) -> str:
        return self._run_cli(args, json_output=False, expected_exit_code=expected_exit_code)

    def run_json(
        self,
        command_key: str,
        args: list[str],
        *,
        expected_exit_code: int = 0,
        validate_schema: bool = True,
    ) -> Any:
        payload = self._run_cli(args, json_output=True, expected_exit_code=expected_exit_code)
        if validate_schema:
            schema_name = self.command_schemas.get(command_key)
            if schema_name:
                _validate_schema(self.schema_catalog, schema_name, payload)
        return payload

    @staticmethod
    def _run_cli(
        args: list[str],
        *,
        json_output: bool,
        expected_exit_code: int,
    ) -> Any:
        cmd = [sys.executable, "-m", "ticktick_cli", *args]
        if json_output and "--json" not in args:
            cmd.append("--json")

        env = os.environ.copy()
        pythonpath = env.get("PYTHONPATH")
        src_path = str(ROOT_DIR / "src")
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{pythonpath}" if pythonpath else src_path

        completed = subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            env=env,
        )

        if completed.returncode != expected_exit_code:
            pytest.fail(
                "CLI command failed\n"
                f"Command: {' '.join(cmd)}\n"
                f"Exit code: {completed.returncode}\n"
                f"STDOUT:\n{completed.stdout}\n"
                f"STDERR:\n{completed.stderr}"
            )

        if not json_output:
            return completed.stdout

        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            pytest.fail(
                "Expected JSON output but parsing failed\n"
                f"Command: {' '.join(cmd)}\n"
                f"STDOUT:\n{completed.stdout}\n"
                f"STDERR:\n{completed.stderr}\n"
                f"Error: {exc}"
            )



def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))



def _validate_schema(schema_catalog: dict[str, Any], schema_name: str, payload: Any) -> None:
    schema = {
        "$ref": f"#/$defs/{schema_name}",
        "$defs": schema_catalog["$defs"],
    }
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        rendered = "\n".join(
            f"- {'/'.join(map(str, error.path)) or '<root>'}: {error.message}"
            for error in errors[:10]
        )
        pytest.fail(f"Schema validation failed for '{schema_name}':\n{rendered}")


async def _cleanup_live_state(state: LiveState) -> None:
    """Best-effort cleanup to keep the live test account tidy."""
    if not any([
        state.folder_ids,
        state.project_ids,
        state.tag_names,
        state.habit_ids,
        state.task_locations,
    ]):
        return

    _load_e2e_env(override=True)

    from ticktick_cli.commands import _apply_v2_auth_rate_limit_workaround
    from ticktick_sdk.client import TickTickClient

    _apply_v2_auth_rate_limit_workaround()

    try:
        async with TickTickClient.from_settings() as client:
            for habit_id in list(state.habit_ids):
                try:
                    await client.delete_habit(habit_id)
                except Exception:
                    pass

            for task_id, project_id in list(state.task_locations.items()):
                try:
                    await client.delete_task(task_id, project_id)
                except Exception:
                    pass

            for project_id in list(state.project_ids):
                try:
                    await client.delete_project(project_id)
                except Exception:
                    pass

            for folder_id in list(state.folder_ids):
                try:
                    await client.delete_folder(folder_id)
                except Exception:
                    pass

            for tag_name in list(state.tag_names):
                try:
                    await client.delete_tag(tag_name)
                except Exception:
                    pass
    except Exception:
        pass


@pytest.fixture(scope="session")
def schema_catalog() -> dict[str, Any]:
    return _read_json(REF_DIR / "output_schemas.json")


@pytest.fixture(scope="session")
def command_surface_manifest() -> dict[str, Any]:
    return _read_json(REF_DIR / "command_surface.json")


@pytest.fixture(scope="session")
def e2e_enabled() -> None:
    _load_e2e_env(override=True)

    if os.getenv("TICKTICK_RUN_E2E") != "1":
        pytest.skip("Set TICKTICK_RUN_E2E=1 to run live CLI E2E tests.")

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        pytest.skip(
            "Missing required env vars for E2E tests "
            f"(expected in .env.test or process env): {', '.join(missing)}"
        )


@pytest.fixture
def cli(schema_catalog: dict[str, Any]) -> CLIRunner:
    return CLIRunner(schema_catalog)


@pytest.fixture
def live_state(e2e_enabled: None) -> LiveState:
    prefix = f"cli-e2e-{date.today().strftime('%Y%m%d')}-{secrets.token_hex(4)}"
    state = LiveState(prefix=prefix)
    yield state
    asyncio.run(_cleanup_live_state(state))


@pytest.fixture
def write_json_file(tmp_path: Path) -> Callable[[str, Any], str]:
    def _write(filename: str, payload: Any) -> str:
        path = tmp_path / filename
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)

    return _write


@pytest.fixture
def eventually() -> Callable[[Callable[[], None], float, float], None]:
    def _eventually(assertion: Callable[[], None], timeout: float = 30.0, interval: float = 1.0) -> None:
        deadline = time.monotonic() + timeout
        last_error: AssertionError | None = None

        while time.monotonic() < deadline:
            try:
                assertion()
                return
            except AssertionError as exc:
                last_error = exc
                time.sleep(interval)

        if last_error is not None:
            raise last_error
        raise AssertionError("Condition did not become true before timeout")

    return _eventually

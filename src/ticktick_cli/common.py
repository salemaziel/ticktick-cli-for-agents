"""Shared helpers for the ticktick-cli app."""

from __future__ import annotations

from pathlib import Path


def load_dotenv_if_available() -> None:
    """Load a nearby .env file when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv

        cwd = Path.cwd()
        for parent in [cwd, *cwd.parents]:
            env_file = parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                return
        load_dotenv()
    except ImportError:
        pass


def get_version() -> str:
    """Get installed ticktick-cli version."""
    try:
        from importlib.metadata import version

        return version("ticktick-cli")
    except Exception:
        return "unknown"

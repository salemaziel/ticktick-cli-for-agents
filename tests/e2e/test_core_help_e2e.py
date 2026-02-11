"""Core non-mutating CLI E2E smoke checks."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
@pytest.mark.e2e_core
def test_auth_help(cli, e2e_enabled: None) -> None:
    auth_help = cli.run_text(["auth", "--help"])

    assert "usage:" in auth_help.lower()
    assert "manual" in auth_help.lower()

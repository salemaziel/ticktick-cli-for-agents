"""Live E2E tests for user and focus command areas."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
@pytest.mark.e2e_user
def test_user_commands_return_realistic_payloads(cli, e2e_enabled: None) -> None:
    profile = cli.run_json("user profile", ["user", "profile"])
    status = cli.run_json("user status", ["user", "status"])
    statistics = cli.run_json("user statistics", ["user", "statistics"])
    preferences = cli.run_json("user preferences", ["user", "preferences"])

    assert isinstance(profile["profile"], dict)
    assert len(profile["profile"]) > 0

    assert isinstance(status["status"], dict)
    assert len(status["status"]) > 0

    assert isinstance(statistics["statistics"], dict)
    assert len(statistics["statistics"]) > 0

    assert isinstance(preferences["preferences"], dict)
    assert len(preferences["preferences"]) > 0


@pytest.mark.e2e
@pytest.mark.e2e_focus
def test_focus_commands_consistent_counts(cli, e2e_enabled: None) -> None:
    heatmap = cli.run_json("focus heatmap", ["focus", "heatmap", "--days", "14"])
    by_tag = cli.run_json("focus by-tag", ["focus", "by-tag", "--days", "14"])

    assert isinstance(heatmap["heatmap"], list)
    assert heatmap["count"] == len(heatmap["heatmap"])

    assert isinstance(by_tag["focus_by_tag"], dict)
    assert by_tag["tag_count"] == len(by_tag["focus_by_tag"])

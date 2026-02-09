"""Live E2E tests for habit command area."""

from __future__ import annotations

from datetime import date, timedelta

import pytest


@pytest.mark.e2e
@pytest.mark.e2e_habits
def test_habits_flow_with_realistic_data(cli, live_state, write_json_file, eventually) -> None:
    habit_name = f"{live_state.prefix}-Morning Walk"
    updated_habit_name = f"{habit_name} Daily"

    create_payload = cli.run_json(
        "habits create",
        [
            "habits",
            "create",
            habit_name,
            "--type",
            "Boolean",
            "--goal",
            "1.0",
            "--unit",
            "Count",
            "--target-days",
            "7",
            "--encouragement",
            "Keep consistency",
        ],
    )
    habit_id = create_payload["habit"]["id"]
    assert isinstance(habit_id, str)
    assert create_payload["habit"]["name"] == habit_name
    live_state.habit_ids.add(habit_id)

    list_payload = cli.run_json("habits list", ["habits", "list"])
    assert habit_id in {habit["id"] for habit in list_payload["habits"]}

    get_payload = cli.run_json("habits get", ["habits", "get", habit_id])
    assert get_payload["habit"]["id"] == habit_id
    assert get_payload["habit"]["name"] == habit_name

    update_payload = cli.run_json(
        "habits update",
        [
            "habits",
            "update",
            habit_id,
            "--name",
            updated_habit_name,
            "--target-days",
            "14",
            "--encouragement",
            "Great momentum",
        ],
    )
    assert update_payload["habit"]["id"] == habit_id
    assert update_payload["habit"]["name"] == updated_habit_name

    sections_payload = cli.run_json("habits sections", ["habits", "sections"])
    assert sections_payload["count"] == len(sections_payload["sections"])

    preferences_payload = cli.run_json("habits preferences", ["habits", "preferences"])
    assert isinstance(preferences_payload["preferences"], dict)

    today = date.today()
    yesterday = today - timedelta(days=1)

    checkin_payload = cli.run_json(
        "habits checkin",
        ["habits", "checkin", habit_id, "--value", "1.0", "--date", today.isoformat()],
    )
    assert checkin_payload["habit"]["id"] == habit_id

    batch_file = write_json_file(
        "habit-batch-checkins.json",
        [{"habit_id": habit_id, "value": 1.0, "checkin_date": yesterday.isoformat()}],
    )
    batch_payload = cli.run_json("habits batch-checkin", ["habits", "batch-checkin", "--file", batch_file])
    assert batch_payload["count"] >= 1
    assert habit_id in batch_payload["result"]

    checkins_payload = cli.run_json("habits checkins", ["habits", "checkins", habit_id, "--after-stamp", "0"])
    assert habit_id in checkins_payload["checkins"]

    archive_payload = cli.run_json("habits archive", ["habits", "archive", habit_id])
    assert archive_payload["habit"]["id"] == habit_id

    unarchive_payload = cli.run_json("habits unarchive", ["habits", "unarchive", habit_id])
    assert unarchive_payload["habit"]["id"] == habit_id

    delete_payload = cli.run_json("habits delete", ["habits", "delete", habit_id])
    assert delete_payload["habit_id"] == habit_id
    live_state.habit_ids.discard(habit_id)

    def _habit_deleted() -> None:
        payload = cli.run_json("habits list", ["habits", "list"])
        assert habit_id not in {habit["id"] for habit in payload["habits"]}

    eventually(_habit_deleted, timeout=20.0, interval=1.0)

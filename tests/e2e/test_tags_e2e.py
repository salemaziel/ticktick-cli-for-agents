"""Live E2E tests for tag management commands."""

from __future__ import annotations

import pytest


@pytest.mark.e2e
@pytest.mark.e2e_tags
def test_tags_flow_with_content_assertions(cli, live_state, eventually) -> None:
    source_name = f"{live_state.prefix}-home-errands"
    renamed_source = f"{source_name}-renamed"
    target_name = f"{live_state.prefix}-important"

    source_create = cli.run_json("tags create", ["tags", "create", source_name, "--color", "#F18181"])
    assert source_create["tag"]["name"] == source_name
    assert source_create["tag"]["color"] == "#F18181"
    live_state.tag_names.add(source_name)

    source_update = cli.run_json("tags update", ["tags", "update", source_name, "--color", "#57A8FF"])
    assert source_update["tag"]["name"] == source_name
    assert source_update["tag"]["color"] == "#57A8FF"

    source_rename = cli.run_json("tags rename", ["tags", "rename", source_name, renamed_source])
    assert source_rename["old_name"] == source_name
    assert source_rename["new_name"] == renamed_source
    live_state.tag_names.discard(source_name)
    live_state.tag_names.add(renamed_source)

    target_create = cli.run_json("tags create", ["tags", "create", target_name, "--color", "#97E38B"])
    assert target_create["tag"]["name"] == target_name
    live_state.tag_names.add(target_name)

    def _renamed_visible() -> None:
        payload = cli.run_json("tags list", ["tags", "list"])
        names = {item["name"] for item in payload["tags"]}
        assert renamed_source in names

    eventually(_renamed_visible, timeout=20.0, interval=1.0)

    merge_payload = cli.run_json("tags merge", ["tags", "merge", renamed_source, target_name])
    assert merge_payload["source"] == renamed_source
    assert merge_payload["target"] == target_name
    live_state.tag_names.discard(renamed_source)

    def _source_merged_away() -> None:
        payload = cli.run_json("tags list", ["tags", "list"])
        names = {item["name"] for item in payload["tags"]}
        assert renamed_source not in names

    eventually(_source_merged_away, timeout=20.0, interval=1.0)

    delete_payload = cli.run_json("tags delete", ["tags", "delete", target_name])
    assert delete_payload["name"] == target_name
    live_state.tag_names.discard(target_name)

    def _target_deleted() -> None:
        payload = cli.run_json("tags list", ["tags", "list"])
        names = {item["name"] for item in payload["tags"]}
        assert target_name not in names

    eventually(_target_deleted, timeout=20.0, interval=1.0)

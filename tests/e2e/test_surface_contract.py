"""Contract tests for CLI command surface references (no live account needed)."""

from __future__ import annotations

import argparse

from ticktick_cli.parser import create_parser


def _parser_command_surface() -> tuple[set[str], dict[str, set[str]]]:
    parser = create_parser()
    subparsers_action = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    single: set[str] = set()
    grouped: dict[str, set[str]] = {}

    for command, command_parser in subparsers_action.choices.items():
        nested_action = next(
            (
                action
                for action in command_parser._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if nested_action is None:
            single.add(command)
        else:
            grouped[command] = set(nested_action.choices.keys())

    return single, grouped


def test_manifest_matches_parser_surface(command_surface_manifest: dict) -> None:
    expected_single = set(command_surface_manifest["single_commands"])
    expected_grouped = {
        group: set(subcommands)
        for group, subcommands in command_surface_manifest["group_commands"].items()
    }

    actual_single, actual_grouped = _parser_command_surface()

    assert actual_single == expected_single
    assert actual_grouped == expected_grouped

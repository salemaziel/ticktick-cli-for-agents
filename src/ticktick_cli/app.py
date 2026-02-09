"""Top-level orchestration for ticktick-cli."""

from __future__ import annotations

import asyncio
import sys
from typing import NoReturn

from ticktick_cli.commands import run_auth, run_data_cli, run_server
from ticktick_cli.common import load_dotenv_if_available
from ticktick_cli.parser import create_parser


def main() -> int | NoReturn:
    """Main entry point for the CLI."""
    load_dotenv_if_available()

    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        return run_server(output_json=args.json)

    if args.command == "server":
        return run_server(
            enabled_tools=args.enabledTools,
            enabled_modules=args.enabledModules,
            host=args.host,
            output_json=args.json,
        )

    if args.command == "auth":
        return run_auth(manual=args.manual, output_json=args.json)

    if args.command in {"tasks", "projects", "folders", "columns", "tags", "user", "focus", "habits"}:
        return asyncio.run(run_data_cli(args))

    parser.print_help()
    return 1


def cli_main() -> NoReturn:
    """CLI entry point that exits with the appropriate code."""
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        sys.exit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

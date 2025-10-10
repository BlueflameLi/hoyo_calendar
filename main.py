"""Command line entrypoint for the hoyo_calendar pipeline."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Sequence

from services.pipeline import run_pipeline
from settings import Settings, get_settings


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="hoyo_calendar maintenance CLI")
    parser.add_argument(
        "command",
        choices=["update"],
        nargs="?",
        default="update",
        help="Action to perform (default: update)",
    )
    parser.add_argument(
        "--data-output-dir",
        type=Path,
        help="Override the JSON output directory",
    )
    parser.add_argument(
        "--ics-output-dir",
        type=Path,
        help="Override the ICS output directory",
    )
    parser.add_argument(
        "--extra-ics-dir",
        action="append",
        type=Path,
        default=None,
        help="Additional ICS directories (can be repeated)",
    )
    parser.add_argument(
        "--debug-mocks",
        action="store_true",
        help="Force enable mock responses regardless of the environment",
    )
    return parser


def build_settings_from_args(args: argparse.Namespace) -> Settings:
    settings = get_settings()
    updates: dict[str, object] = {}
    if args.data_output_dir:
        updates["data_output_dir"] = args.data_output_dir.resolve()
    if args.ics_output_dir:
        updates["ics_output_dir"] = args.ics_output_dir.resolve()
    if args.extra_ics_dir:
        updates["extra_ics_dirs"] = [path.resolve() for path in args.extra_ics_dir]
    if args.debug_mocks:
        updates["enable_debug_mocks"] = True
    if updates:
        settings = settings.model_copy(update=updates)
    return settings


def main(argv: Sequence[str] | None = None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    settings = build_settings_from_args(args)

    if args.command == "update":
        asyncio.run(run_pipeline(settings))


if __name__ == "__main__":
    main()

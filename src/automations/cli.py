from __future__ import annotations

import argparse

from .config import load_config
from .registry import load_automations
from .runner import run_automations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run personal automations")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Config file name in project root (default: config.yaml)",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Only run listed automation ids (comma-separated or repeatable)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Skip listed automation ids (comma-separated or repeatable)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available automations and exit",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(filename=args.config)
    if args.list:
        _print_automations(config)
        return 0

    only = _parse_ids(args.only)
    skip = _parse_ids(args.skip)

    summary = run_automations(config, only=only or None, skip=skip or None)
    _print_summary(summary)
    return 0


def _parse_ids(values: list[str]) -> set[str]:
    ids: set[str] = set()
    for value in values:
        for chunk in value.split(","):
            chunk = chunk.strip()
            if chunk:
                ids.add(chunk)
    return ids


def _print_automations(config) -> None:
    for automation in load_automations():
        settings = config.automation_settings(
            automation.spec.id,
            default_enabled=automation.spec.default_enabled,
        )
        status = "enabled" if settings.enabled else "disabled"
        print(f"{automation.spec.id}: {automation.spec.title} ({status})")
        print(f"  {automation.spec.description}")


def _print_summary(summary) -> None:
    print("Automation results:")
    for result in summary.results:
        message = f" - {result.automation_id}: {result.status}"
        if result.status == "error" and result.message:
            message += f" ({result.message})"
        print(message)

    if summary.report_path:
        print(f"HTML report written: {summary.report_path}")
    else:
        print("HTML report not generated (see run log)")

    if summary.warnings:
        print("Warnings:")
        for warning in summary.warnings:
            print(f"- {warning}")

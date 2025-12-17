from __future__ import annotations

import argparse

from .config import load_config
from .runner import AutomationResult, run_automations


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run personal automations")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Config file name in project root (default: config.yaml)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    config = load_config(filename=args.config)
    result = run_automations(config)

    print(f"GitHub repos: {_format_count(result.repo_count)}")
    print(f"Obsidian markdown files: {_format_count(result.md_count)}")
    if result.html_path:
        print(f"HTML report written: {result.html_path}")
    else:
        print("HTML report not generated (see errors)")

    if result.errors:
        _print_errors(result)

    return 0


def _format_count(value: int | None) -> str:
    return str(value) if value is not None else "N/A"


def _print_errors(result: AutomationResult) -> None:
    print("Automation warnings:")
    for error in result.errors:
        print(f"- {error.step}: {error.message}")

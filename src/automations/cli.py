from __future__ import annotations

import argparse

from .config import load_config
from .runner import run_automations


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
    summary = run_automations(config)
    _print_summary(summary)
    return 0


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

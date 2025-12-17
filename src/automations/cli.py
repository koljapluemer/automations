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
    result = run_automations(config)

    print(f"GitHub repos: {result.repo_count}")
    print(f"Obsidian markdown files: {result.md_count}")
    print(f"HTML report written: {result.html_path}")
    return 0

"""Command-line interface for the file-integrity checker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from integrity_checker import create_baseline, verify_directory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or verify a SHA-256 file-integrity baseline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline_parser = subparsers.add_parser("baseline", help="Create a baseline inventory.")
    baseline_parser.add_argument("directory", type=Path, help="Directory to inventory.")
    baseline_parser.add_argument(
        "--baseline", type=Path, default=Path("baseline.json"),
        help="Output baseline JSON path (default: baseline.json)."
    )

    verify_parser = subparsers.add_parser("verify", help="Verify a directory against a baseline.")
    verify_parser.add_argument("directory", type=Path, help="Directory to verify.")
    verify_parser.add_argument(
        "--baseline", type=Path, default=Path("baseline.json"),
        help="Input baseline JSON path (default: baseline.json)."
    )
    verify_parser.add_argument(
        "--report", type=Path, help="Optional path to save a JSON verification report."
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.command == "baseline":
            document = create_baseline(args.directory, args.baseline)
            print(f"Baseline created: {args.baseline}")
            print(f"Files recorded: {len(document['files'])}")
            return 0

        report = verify_directory(args.directory, args.baseline)
        print(f"Status: {report['status']}")
        print(f"Checked files: {report['checked_files']}")
        print(
            f"Added: {len(report['added'])} | "
            f"Modified: {len(report['modified'])} | "
            f"Missing: {len(report['missing'])}"
        )
        for category in ("added", "modified", "missing"):
            for relative_path in report[category]:
                print(f"  {category.upper()}: {relative_path}")

        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(f"Report saved: {args.report}")

        return 0 if report["status"] == "CLEAN" else 2
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

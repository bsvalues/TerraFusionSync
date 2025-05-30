#!/usr/bin/env python3
"""
TerraFusion Platform SDK CLI

A command-line interface for interacting with TerraFusion Platform SDK tools.
"""
import sys
import os
import argparse
from pathlib import Path

# Add the project root to Python path to allow module imports
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.append(str(PROJECT_ROOT))

def main():
    parser = argparse.ArgumentParser(
        description="TerraFusion Platform SDK CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="SDK command to run"
    )

    # Define 'new-county' subcommand
    county_parser = subparsers.add_parser(
        "new-county",
        help="Create scaffolding for a new county configuration"
    )
    county_parser.add_argument(
        "county_name",
        help="Name of the county (e.g., 'benton', 'franklin')"
    )
    county_parser.add_argument(
        "--legacy-system",
        default="PACS",
        help="Legacy CAMA system type (PACS, TYLER, PATRIOT, etc.)"
    )
    county_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration if it exists"
    )

    # Add more subcommands here as the SDK grows

    args = parser.parse_args()

    if args.command == "new-county":
        from terrafusion_platform.sdk.new_county_setup import main as setup_county
        sys.argv = ["new_county_setup.py", args.county_name]
        if args.legacy_system:
            sys.argv.extend(["--legacy-system", args.legacy_system])
        if args.force:
            sys.argv.append("--force")
        setup_county()
    elif not args.command:
        parser.print_help()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()
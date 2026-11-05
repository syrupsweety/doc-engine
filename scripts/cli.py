#!/usr/bin/env python3
"""Command-line entry point."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import DocEngineRenderer
from loader import ConfigLoader


def main():
    parser = argparse.ArgumentParser(
        description="doc-engine: Render Markdown documents to various formats",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i docs/manuscript.md -o output/paper.pdf -f pdf -p gost-7.32
  %(prog)s -i docs/manuscript.md -o output/paper.html -f html -p ieee
  %(prog)s -i docs/manuscript.md -o output/paper.docx -f docx -p apa-7th
        """,
    )

    parser.add_argument("-i", "--input", help="Input Markdown file path")

    parser.add_argument("-o", "--output", help="Output file path")

    parser.add_argument("-f", "--format", choices=["pdf", "html", "docx"], help="Output format")

    parser.add_argument(
        "-p", "--profile", help="Profile name (use --list-profiles to see available profiles)"
    )

    parser.add_argument("--list-profiles", action="store_true", help="List all available profiles")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    parser.add_argument(
        "--dry-run", action="store_true", help="Print the pandoc command without executing"
    )

    args = parser.parse_args()

    if args.list_profiles:
        profiles = ConfigLoader.discover_profiles()
        if profiles:
            print("Available profiles:")
            for profile in profiles:
                print(f"  - {profile}")
        else:
            print("No valid profiles found.")
        sys.exit(0)

    if not all([args.input, args.output, args.format, args.profile]):
        print("Error: For rendering, you must provide --input, --output, --format, and --profile")
        print("Use --list-profiles to see available profiles")
        sys.exit(1)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    if not ConfigLoader.validate_profile(args.profile):
        print(f"Error: Invalid or incomplete profile: {args.profile}")
        sys.exit(1)

    try:
        renderer = DocEngineRenderer(
            profile_name=args.profile,
            input_file=input_path,
            output_file=Path(args.output),
            format_type=args.format,
        )

        if args.dry_run:
            from builder import CommandBuilder

            command_builder = CommandBuilder(
                args.profile, input_path, Path(args.output), args.format
            )
            cmd = command_builder.build_command()
            print(" ".join(cmd))
            sys.exit(0)

        success = renderer.render()
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Unexpected error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

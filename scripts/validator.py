#!/usr/bin/env python3
"""Profile and dependency validation."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loader import ConfigLoader


def validate_profile(profile_name: str) -> bool:
    """Validate a specific profile."""
    print(f"Validating profile: {profile_name}")

    if not ConfigLoader.validate_profile(profile_name):
        return False

    profile_config = ConfigLoader.load_profile_config(profile_name)
    if not profile_config:
        return False

    if not ConfigLoader.validate_config_structure(profile_config, profile_name):
        return False

    print(f"Profile {profile_name} is valid")
    return True


def validate_all_profiles() -> bool:
    """Validate all available profiles."""
    print("Validating all profiles...")

    profiles = ConfigLoader.discover_profiles()

    if not profiles:
        print("error: No valid profiles found")
        return False

    all_valid = True
    for profile_name in profiles:
        if not validate_profile(profile_name):
            all_valid = False

    if all_valid:
        print("All profiles are valid")
    else:
        print("error: Some profiles have validation errors")

    return all_valid


def validate_config_files() -> bool:
    """Validate all configuration files."""
    print("Validating configuration files...")

    shared_metadata = ConfigLoader.load_shared_metadata()
    if shared_metadata is None:
        print("error: Shared metadata file is invalid")
        return False
    print("Shared metadata is valid")

    all_valid = True
    profiles_dir = Path("profiles")

    for config_file in profiles_dir.rglob("config.yaml"):
        try:
            with open(config_file, encoding="utf-8") as f:
                import yaml

                config = yaml.safe_load(f)

            if not config:
                print(f"error: Empty config file: {config_file}")
                all_valid = False
            else:
                print(f"Config file valid: {config_file}")

        except Exception as e:
            print(f"error: Invalid config file {config_file}: {e}")
            all_valid = False

    return all_valid


def validate_dependencies() -> bool:
    """Validate that all required dependencies are available."""
    print("Validating dependencies...")
    import shutil

    required_tools = ["pandoc"]
    all_available = True

    for tool in required_tools:
        if shutil.which(tool) is None:
            print(f"error: Required tool not found: {tool}")
            all_available = False
        else:
            print(f"Tool available: {tool}")

    return all_available


def main():
    parser = argparse.ArgumentParser(
        description="Validate doc-engine configuration and dependencies"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--profile", help="Validate a specific profile")
    group.add_argument("--all", action="store_true", help="Validate all profiles")
    group.add_argument("--config", action="store_true", help="Validate configuration files")
    group.add_argument("--deps", action="store_true", help="Validate dependencies")

    args = parser.parse_args()

    success = True

    if args.profile:
        success = validate_profile(args.profile)
    elif args.all:
        success = validate_all_profiles()
    elif args.config:
        success = validate_config_files()
    elif args.deps:
        success = validate_dependencies()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

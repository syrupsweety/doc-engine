#!/usr/bin/env python3
"""Profile configuration loading and validation."""

import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).parent))


class ConfigLoader:
    """Handles loading and validation of configuration files."""

    @staticmethod
    def load_shared_metadata() -> dict[str, Any]:
        """Load shared metadata from _shared/metadata.yaml."""
        metadata_file = Path("profiles/_shared/metadata.yaml")

        if not metadata_file.exists():
            return {}

        try:
            with open(metadata_file, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Warning: Error parsing shared metadata: {e}")
            return {}
        except Exception as e:
            print(f"Warning: Error reading shared metadata file: {e}")
            return {}

    @staticmethod
    def load_profile_config(profile_name: str) -> dict[str, Any] | None:
        """Load a profile's configuration with validation."""
        config_path = Path(f"profiles/{profile_name}/config.yaml")

        if not config_path.exists():
            print(f"Error: Profile config not found: {config_path}")
            return None

        try:
            with open(config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                print(f"Error: Profile config is empty: {config_path}")
                return None

            if "name" not in config:
                print(f"Warning: Profile config missing 'name' field: {config_path}")

            if "output_formats" not in config:
                print(f"Warning: Profile config missing 'output_formats' section: {config_path}")

            return config

        except yaml.YAMLError as e:
            print(f"Error: Invalid YAML in profile config: {config_path}")
            print(f"YAML Error: {e}")
            return None
        except Exception as e:
            print(f"Error: Failed to read profile config: {config_path}")
            print(f"File Error: {e}")
            return None

    @staticmethod
    def merge_metadata(
        profile_config: dict[str, Any], shared_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge shared, per-profile and profile metadata; profile wins."""
        merged = {}

        merged.update(shared_metadata or {})

        profile_defaults = ConfigLoader.get_profile_defaults(profile_config.get("name", ""))
        merged.update(profile_defaults)

        if "metadata_defaults" in profile_config:
            merged.update(profile_config["metadata_defaults"])

        return merged

    @staticmethod
    def validate_config_structure(config: dict[str, Any], profile_name: str) -> bool:
        """Validate the structure of a profile configuration."""
        errors = []

        required_fields = ["name", "output_formats"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")

        if "output_formats" in config:
            for format_name in config["output_formats"]:
                if format_name not in ["pdf", "html", "docx"]:
                    errors.append(f"Unknown output format: {format_name}")

        if errors:
            print(f"Configuration validation errors for {profile_name}:")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    @staticmethod
    def get_output_config(profile_config: dict[str, Any], format_type: str) -> dict[str, Any]:
        """Get output format configuration for a specific format."""
        output_formats = profile_config.get("output_formats", {})
        return output_formats.get(format_type, {})

    @staticmethod
    def get_bibliography_method(profile_config: dict[str, Any], format_type: str) -> str:
        """Get bibliography method for a specific format."""
        output_config = ConfigLoader.get_output_config(profile_config, format_type)
        return output_config.get("bibliography_method", "csl")

    @staticmethod
    def get_template_path(profile_name: str, format_type: str) -> Path | None:
        """Get the template path for a profile and format."""
        profile_config = ConfigLoader.load_profile_config(profile_name)
        if not profile_config:
            return None

        output_config = ConfigLoader.get_output_config(profile_config, format_type)
        template_name = output_config.get("template")

        if template_name:
            profile_path = Path(f"profiles/{profile_name}")
            template_path = profile_path / template_name
            if template_path.exists():
                return template_path

        return None

    @staticmethod
    def get_profile_defaults(profile_name: str) -> dict[str, Any]:
        """Get default metadata for a specific profile."""
        defaults = {
            "lang": "en-US",
            "fontsize": "12pt",
            "linestretch": "1.5",
            "papersize": "a4",
            "geometry": "left=3cm,right=1.5cm,top=2cm,bottom=2cm",
        }

        return defaults

    @staticmethod
    def validate_profile(profile_name: str) -> bool:
        """Validate that a profile exists and has required files."""
        profile_path = Path(f"profiles/{profile_name}")
        config_path = profile_path / "config.yaml"

        if not profile_path.exists():
            print(f"Profile directory not found: {profile_path}")
            return False

        if not config_path.exists():
            print(f"Profile config not found: {config_path}")
            return False

        config = ConfigLoader.load_profile_config(profile_name)
        if not config:
            return False

        return True

    @staticmethod
    def ensure_output_dir(output_path: Path) -> None:
        """Ensure the output directory exists."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def discover_profiles() -> list:
        """Discover all available profiles by scanning the profiles directory."""
        profiles_dir = Path("profiles")
        if not profiles_dir.exists():
            return []

        profile_dirs = [d for d in profiles_dir.iterdir() if d.is_dir() and d.name != "_shared"]

        valid_profiles = []
        for profile_dir in profile_dirs:
            if ConfigLoader.validate_profile(profile_dir.name):
                valid_profiles.append(profile_dir.name)

        return sorted(valid_profiles)

#!/usr/bin/env python3
"""Smoke tests for the renderer."""

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine import DocEngineRenderer
from loader import ConfigLoader


def test_basic_functionality() -> bool:
    """Test basic functionality without actual rendering."""
    print("Testing basic functionality...")

    try:
        config = ConfigLoader.load_profile_config("ieee")
        if not config:
            print("error: Failed to load IEEE profile config")
            return False
        print("Profile configuration loading works")
    except Exception as e:
        print(f"error: Error loading profile config: {e}")
        return False

    try:
        ConfigLoader.load_shared_metadata()
        print("Shared metadata loading works")
    except Exception as e:
        print(f"error: Error loading shared metadata: {e}")
        return False

    if not ConfigLoader.validate_profile("ieee"):
        print("error: IEEE profile validation failed")
        return False
    print("Profile validation works")

    return True


def test_profile_rendering(profile_name: str, format_type: str) -> bool:
    """Test rendering for a specific profile and format."""
    print(f"Testing {profile_name} profile with {format_type} format...")

    test_content = """---
title: "Test Document"
author: "Test Author"
---

# Introduction

This is a test document for validation.

## Test Section

This section contains some content.

### Test Subsection

More content here.
"""

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "test.md"
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            output_file = Path(temp_dir) / f"test.{format_type}"

            renderer = DocEngineRenderer(
                profile_name=profile_name,
                input_file=input_file,
                output_file=output_file,
                format_type=format_type,
            )
            if not renderer.render():
                return False
            if not output_file.exists():
                print(f"error: {output_file} was not created")
                return False

            print(f"{profile_name} / {format_type}: ok")
            return True

    except Exception as e:
        print(f"error: cannot test {profile_name} / {format_type}: {e}")
        return False


def test_all_profiles() -> bool:
    """Test all available profiles."""
    print("Testing all profiles...")

    profiles = ConfigLoader.discover_profiles()

    if not profiles:
        print("error: No valid profiles found")
        return False

    all_passed = True

    for profile in profiles:
        if not ConfigLoader.validate_profile(profile):
            print(f"error: {profile} profile validation failed")
            all_passed = False
            continue

        if not test_profile_rendering(profile, "html"):
            all_passed = False

    if all_passed:
        print("All profiles passed basic tests")
    else:
        print("error: Some profiles failed tests")

    return all_passed


def test_rendering_pipeline() -> bool:
    """Test the complete rendering pipeline."""
    print("Testing rendering pipeline...")

    test_content = """---
title: "Pipeline Test"
---

# Test Document

This tests the complete rendering pipeline.
"""

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "pipeline_test.md"
            with open(input_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            output_file = Path(temp_dir) / "pipeline_test.html"

            renderer = DocEngineRenderer(
                profile_name="ieee",
                input_file=input_file,
                output_file=output_file,
                format_type="html",
            )

            success = renderer.render()

            if success:
                print("Rendering pipeline works")
                return True
            else:
                print("⚠ Rendering pipeline failed (Pandoc may not be available)")
                return False

    except Exception as e:
        print(f"error: Error in rendering pipeline test: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for doc-engine")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--basic", action="store_true", help="Run basic functionality tests")
    group.add_argument("--profiles", action="store_true", help="Test all profiles")
    group.add_argument("--render", action="store_true", help="Test rendering pipeline")

    args = parser.parse_args()

    success = True

    if args.basic:
        success = test_basic_functionality()
    elif args.profiles:
        success = test_all_profiles()
    elif args.render:
        success = test_rendering_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

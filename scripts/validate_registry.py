#!/usr/bin/env python3
"""Validate runbook routing registry.

This script validates the runbook registry (_registry.yaml) to ensure:
1. Registry YAML schema is valid
2. All referenced runbook files exist
3. No routing collisions (same selectors + same priority)
4. No unreachable runbooks (lower priority with same selectors)

Usage:
    python scripts/validate_registry.py
    python scripts/validate_registry.py --registry runbooks/_registry.yaml
"""

import argparse
import sys
from pathlib import Path

import yaml


def validate_schema(registry_data: dict) -> tuple[bool, list[str]]:
    """Validate registry schema.

    Args:
        registry_data: Parsed registry YAML data

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check required top-level fields
    if "registry_version" not in registry_data:
        errors.append("Missing required field: registry_version")

    if "runbooks" not in registry_data:
        errors.append("Missing required field: runbooks")
        return False, errors

    # Validate each runbook entry
    for i, entry in enumerate(registry_data["runbooks"]):
        entry_id = entry.get("id", f"<entry {i}>")

        # Required fields
        required_fields = ["id", "name", "path", "selectors", "priority", "enabled"]
        for field in required_fields:
            if field not in entry:
                errors.append(f"  ❌ {entry_id}: Missing required field '{field}'")

        # Validate selectors
        if "selectors" in entry:
            selectors = entry["selectors"]
            if not isinstance(selectors, dict):
                errors.append(f"  ❌ {entry_id}: 'selectors' must be a dict")
            elif not selectors:
                errors.append(f"  ❌ {entry_id}: 'selectors' cannot be empty")

        # Validate priority
        if "priority" in entry:
            if not isinstance(entry["priority"], int):
                errors.append(f"  ❌ {entry_id}: 'priority' must be an integer")

        # Validate enabled
        if "enabled" in entry:
            if not isinstance(entry["enabled"], bool):
                errors.append(f"  ❌ {entry_id}: 'enabled' must be a boolean")

    return len(errors) == 0, errors


def validate_file_existence(
    registry_data: dict, repo_root: Path
) -> tuple[bool, list[str]]:
    """Validate that all referenced runbook files exist.

    Args:
        registry_data: Parsed registry YAML data
        repo_root: Path to repository root

    Returns:
        Tuple of (all_exist, error_messages)
    """
    errors = []

    for entry in registry_data.get("runbooks", []):
        entry_id = entry.get("id", "<unknown>")
        path = entry.get("path")

        if not path:
            continue

        file_path = repo_root / path

        if not file_path.exists():
            errors.append(f"  ❌ {entry_id}: File not found: {path}")

    return len(errors) == 0, errors


def validate_collisions(registry_data: dict) -> tuple[bool, list[str]]:
    """Detect routing collisions (same selectors + same priority).

    Args:
        registry_data: Parsed registry YAML data

    Returns:
        Tuple of (no_collisions, error_messages)
    """
    errors = []
    warnings = []

    # Group runbooks by selectors
    selector_groups: dict[str, list[dict]] = {}

    for entry in registry_data.get("runbooks", []):
        if not entry.get("enabled", True):
            continue

        # Create a hashable key from selectors
        selectors = entry.get("selectors", {})
        selector_key = tuple(sorted(selectors.items()))

        if selector_key not in selector_groups:
            selector_groups[selector_key] = []

        selector_groups[selector_key].append(entry)

    # Check for collisions within each group
    for selector_key, entries in selector_groups.items():
        if len(entries) == 1:
            continue

        # Group by priority
        priority_groups: dict[int, list[str]] = {}
        for entry in entries:
            priority = entry.get("priority", 0)
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(entry["id"])

        # Check for same priority (collision)
        for priority, runbook_ids in priority_groups.items():
            if len(runbook_ids) > 1:
                errors.append(
                    f"  ❌ COLLISION: Multiple runbooks with same selectors "
                    f"and priority {priority}:\n"
                    f"     {', '.join(runbook_ids)}\n"
                    f"     Selectors: {dict(selector_key)}"
                )

        # Warn about unreachable runbooks (lower priority)
        if len(priority_groups) > 1:
            sorted_priorities = sorted(priority_groups.keys(), reverse=True)
            highest = sorted_priorities[0]
            for lower_priority in sorted_priorities[1:]:
                warnings.append(
                    f"  ⚠️  UNREACHABLE: Runbooks with priority "
                    f"{lower_priority} will never be reached:\n"
                    f"     {', '.join(priority_groups[lower_priority])}\n"
                    f"     (Higher priority {highest}: "
                    f"{', '.join(priority_groups[highest])})"
                )

    # Print warnings
    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(warning)

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate runbook routing registry")
    parser.add_argument(
        "--registry",
        default="runbooks/_registry.yaml",
        help="Path to registry file (default: runbooks/_registry.yaml)",
    )
    args = parser.parse_args()

    registry_path = Path(args.registry)
    if not registry_path.exists():
        print(f"❌ Registry file not found: {registry_path}")
        return 1

    # Determine repo root (parent of runbooks directory)
    repo_root = registry_path.parent.parent

    print("=" * 80)
    print("Runbook Registry Validation")
    print("=" * 80)
    print(f"Registry: {registry_path}")
    print(f"Repo root: {repo_root}")
    print()

    # Load registry
    try:
        with open(registry_path) as f:
            registry_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Failed to parse registry YAML: {e}")
        return 1

    # Run validations
    all_valid = True

    # 1. Schema validation
    print("📋 Validating schema...")
    schema_valid, schema_errors = validate_schema(registry_data)
    if schema_valid:
        print("  ✅ Schema is valid")
    else:
        print("  ❌ Schema validation failed:")
        for error in schema_errors:
            print(f"    {error}")
        all_valid = False

    # 2. File existence validation
    print("\n📁 Validating file existence...")
    files_valid, file_errors = validate_file_existence(registry_data, repo_root)
    if files_valid:
        runbook_count = len(registry_data.get("runbooks", []))
        print(f"  ✅ All {runbook_count} runbook files exist")
    else:
        print("  ❌ File validation failed:")
        for error in file_errors:
            print(f"    {error}")
        all_valid = False

    # 3. Collision detection
    print("\n🔍 Detecting routing collisions...")
    no_collisions, collision_errors = validate_collisions(registry_data)
    if no_collisions:
        print("  ✅ No routing collisions detected")
    else:
        print("  ❌ Routing collisions detected:")
        for error in collision_errors:
            print(f"    {error}")
        all_valid = False

    # Summary
    print("\n" + "=" * 80)
    if all_valid:
        print("✅ Registry validation PASSED")
        return 0
    else:
        print("❌ Registry validation FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())


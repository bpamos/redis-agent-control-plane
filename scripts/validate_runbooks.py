#!/usr/bin/env python3
"""Validate runbooks against actual Redis Enterprise documentation.

This script validates that runbooks contain accurate information by:
1. Verifying all doc_refs point to real files in ../docs/
2. Checking that runbooks are marked as validated
3. Verifying version information is present
4. Listing all validation metadata

Usage:
    python scripts/validate_runbooks.py
    python scripts/validate_runbooks.py --runbook runbooks/redis_enterprise/vm/single_node.yaml
"""

import argparse
import sys
from pathlib import Path

import yaml


def validate_doc_refs(runbook_data: dict, docs_base: Path) -> tuple[bool, list[str]]:
    """Validate that all doc_refs point to real files.

    Args:
        runbook_data: Parsed runbook YAML data
        docs_base: Base path to docs directory

    Returns:
        Tuple of (all_valid, error_messages)
    """
    errors = []
    runbook = runbook_data["runbook"]

    for step in runbook.get("steps", []):
        step_id = step["id"]
        doc_refs = step.get("doc_refs", [])

        for doc_ref in doc_refs:
            doc_path = docs_base / doc_ref["path"]

            if not doc_path.exists():
                errors.append(
                    f"  ❌ {step_id}: doc_ref '{doc_ref['path']}' - FILE NOT FOUND"
                )

    return len(errors) == 0, errors


def validate_runbook_metadata(runbook_data: dict) -> tuple[bool, list[str]]:
    """Validate runbook metadata (version, validation status, etc.).

    Args:
        runbook_data: Parsed runbook YAML data

    Returns:
        Tuple of (all_valid, error_messages)
    """
    errors = []
    runbook = runbook_data["runbook"]

    # Check for validation metadata
    if not runbook.get("validated"):
        errors.append("  ❌ Runbook not marked as validated")

    if not runbook.get("validation_date"):
        errors.append("  ❌ Runbook missing validation_date")

    if not runbook.get("redis_version"):
        errors.append("  ❌ Runbook missing redis_version")

    # Check version format
    version = runbook.get("version", "")
    if not version or version == "1.0.0":
        errors.append(
            f"  ⚠️  Runbook version is {version} - may be unvalidated placeholder"
        )

    return len(errors) == 0, errors


def validate_runbook(runbook_path: Path, docs_base: Path) -> bool:
    """Validate a single runbook.

    Args:
        runbook_path: Path to runbook YAML file
        docs_base: Base path to docs directory

    Returns:
        True if validation passed, False otherwise
    """
    print(f"\n📄 Validating: {runbook_path}")

    if not runbook_path.exists():
        print(f"  ❌ Runbook file not found: {runbook_path}")
        return False

    # Load runbook
    with open(runbook_path) as f:
        data = yaml.safe_load(f)

    runbook = data["runbook"]

    # Print runbook info
    print(f"  ID: {runbook['id']}")
    print(f"  Name: {runbook['name']}")
    print(f"  Version: {runbook.get('version', 'N/A')}")
    print(f"  Redis Version: {runbook.get('redis_version', 'N/A')}")
    print(f"  Validated: {runbook.get('validated', False)}")
    print(f"  Validation Date: {runbook.get('validation_date', 'N/A')}")

    # Validate metadata
    metadata_valid, metadata_errors = validate_runbook_metadata(data)
    if not metadata_valid:
        print("\n  Metadata validation errors:")
        for error in metadata_errors:
            print(error)

    # Validate doc_refs
    doc_refs_valid, doc_ref_errors = validate_doc_refs(data, docs_base)
    if not doc_refs_valid:
        print("\n  Doc ref validation errors:")
        for error in doc_ref_errors:
            print(error)
    else:
        doc_ref_count = sum(
            len(step.get("doc_refs", [])) for step in runbook.get("steps", [])
        )
        print(f"\n  ✅ All {doc_ref_count} doc_refs are valid")

    # Overall result
    all_valid = metadata_valid and doc_refs_valid
    if all_valid:
        print("\n  ✅ Runbook validation PASSED")
    else:
        print("\n  ❌ Runbook validation FAILED")

    return all_valid


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Redis Enterprise runbooks")
    parser.add_argument(
        "--runbook", help="Path to specific runbook to validate (optional)"
    )
    parser.add_argument(
        "--docs-path",
        default="../docs/content",
        help="Path to docs directory (default: ../docs/content)",
    )
    args = parser.parse_args()

    docs_base = Path(args.docs_path)
    if not docs_base.exists():
        print(f"❌ Docs directory not found: {docs_base}")
        return 1

    print("=" * 80)
    print("Redis Enterprise Runbook Validation")
    print("=" * 80)

    # Determine which runbooks to validate
    if args.runbook:
        runbooks = [Path(args.runbook)]
    else:
        # Validate all Redis Enterprise runbooks (VM, Kubernetes, and Database)
        runbooks = []
        runbooks.extend(Path("runbooks/redis_enterprise/vm").glob("*.yaml"))
        runbooks.extend(Path("runbooks/redis_enterprise/kubernetes").glob("*.yaml"))
        runbooks.extend(Path("runbooks/redis_enterprise/database").glob("*.yaml"))

    if not runbooks:
        print("❌ No runbooks found to validate")
        return 1

    # Validate each runbook
    results = {}
    for runbook_path in runbooks:
        results[runbook_path] = validate_runbook(runbook_path, docs_base)

    # Summary
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for runbook_path, valid in results.items():
        status = "✅ PASS" if valid else "❌ FAIL"
        print(f"{status}: {runbook_path}")

    print(f"\nTotal: {len(results)} runbooks")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


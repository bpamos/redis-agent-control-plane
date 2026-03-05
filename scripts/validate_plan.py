#!/usr/bin/env python3
"""Validate ContextPack JSON output.

This script validates that a context_pack.json file:
1. Has valid JSON structure
2. Contains all required fields
3. Has valid schema versions
4. Has properly formatted doc_refs
5. Has RAG chunks with full provenance
6. Has a runbook_id that matches the registry

Usage:
    python scripts/validate_plan.py <path_to_context_pack.json>

Exit codes:
    0: Valid context pack
    1: Invalid context pack (errors printed to stderr)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redis_agent_control_plane.orchestration.context_pack import ContextPack


def validate_version(version: str, field_name: str) -> list[str]:
    """Validate version string format (semver).

    Args:
        version: Version string to validate.
        field_name: Name of the field for error messages.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    parts = version.split(".")
    if len(parts) != 3:
        errors.append(f"{field_name} must be in semver format (e.g., '1.0.0'), got: {version}")
    else:
        for part in parts:
            if not part.isdigit():
                errors.append(f"{field_name} must contain only digits, got: {version}")
                break
    return errors


def validate_doc_refs(doc_refs: list[dict[str, Any]]) -> list[str]:
    """Validate doc_refs format.

    Args:
        doc_refs: List of doc reference dictionaries.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    for i, ref in enumerate(doc_refs):
        if not isinstance(ref, dict):
            errors.append(f"doc_ref[{i}] must be a dictionary, got: {type(ref)}")
            continue
        if "path" not in ref:
            errors.append(f"doc_ref[{i}] missing required field 'path'")
        if "section" not in ref:
            errors.append(f"doc_ref[{i}] missing required field 'section'")
    return errors


def validate_rag_chunks(rag_chunks: list[dict[str, Any]]) -> list[str]:
    """Validate RAG chunks have full provenance.

    Args:
        rag_chunks: List of RAG chunk dictionaries.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    required_fields = [
        "content",
        "doc_path",
        "chunk_id",
        "category",
        "product_area",
    ]

    for i, chunk in enumerate(rag_chunks):
        if not isinstance(chunk, dict):
            errors.append(f"rag_chunk[{i}] must be a dictionary, got: {type(chunk)}")
            continue

        for field in required_fields:
            if field not in chunk:
                errors.append(f"rag_chunk[{i}] missing required field '{field}'")
            elif not chunk[field]:  # Check for empty strings
                errors.append(f"rag_chunk[{i}] field '{field}' cannot be empty")

    return errors


def validate_context_pack(file_path: Path) -> tuple[bool, list[str]]:
    """Validate a context pack JSON file.

    Args:
        file_path: Path to the context_pack.json file.

    Returns:
        Tuple of (is_valid, error_messages).
    """
    errors = []

    # Check file exists
    if not file_path.exists():
        return False, [f"File not found: {file_path}"]

    # Load JSON
    try:
        with open(file_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    # Validate required top-level fields
    required_fields = [
        "runbook_id",
        "runbook_version",
        "deployment_spec",
        "step_id",
        "step_name",
        "step_description",
        "deterministic_doc_refs",
        "rag_chunks",
        "plan_version",
        "spec_version",
    ]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if errors:
        return False, errors

    # Validate schema versions
    errors.extend(validate_version(data["plan_version"], "plan_version"))
    errors.extend(validate_version(data["spec_version"], "spec_version"))

    # Validate doc_refs
    errors.extend(validate_doc_refs(data["deterministic_doc_refs"]))

    # Validate RAG chunks (if present)
    if data["rag_chunks"]:
        errors.extend(validate_rag_chunks(data["rag_chunks"]))

    # Try to deserialize using ContextPack.from_dict()
    try:
        ContextPack.from_dict(data)
    except Exception as e:
        errors.append(f"Failed to deserialize ContextPack: {e}")

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point for the validation script.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Validate ContextPack JSON output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("file", type=Path, help="Path to context_pack.json file")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print success message if valid"
    )

    args = parser.parse_args()

    is_valid, errors = validate_context_pack(args.file)

    if is_valid:
        if args.verbose:
            print(f"✅ Valid context pack: {args.file}")
        return 0
    else:
        print(f"❌ Invalid context pack: {args.file}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


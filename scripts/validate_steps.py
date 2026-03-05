#!/usr/bin/env python3
"""Validate all step YAML files in the steps/ directory.

This script checks:
- Step files exist and are valid YAML
- Required fields are present
- Parameters are properly defined
- Schema is correct
"""

import sys
from pathlib import Path

import yaml


def validate_step_file(step_path: Path) -> tuple[bool, list[str]]:
    """Validate a single step YAML file.

    Args:
        step_path: Path to step YAML file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check file exists
    if not step_path.exists():
        return False, [f"File not found: {step_path}"]

    # Load YAML
    try:
        with open(step_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML: {e}"]

    # Check top-level structure
    if not data or "step" not in data:
        errors.append("Missing 'step' key")
        return False, errors

    step = data["step"]

    # Check required fields
    required_fields = ["id", "name", "description"]
    for field in required_fields:
        if field not in step:
            errors.append(f"Missing required field: {field}")

    # Validate parameters if present
    if "parameters" in step:
        if not isinstance(step["parameters"], list):
            errors.append("'parameters' must be a list")
        else:
            for i, param in enumerate(step["parameters"]):
                if not isinstance(param, dict):
                    errors.append(f"Parameter {i} must be a dict")
                    continue

                # Check required parameter fields
                if "name" not in param:
                    errors.append(f"Parameter {i} missing 'name'")
                if "type" not in param:
                    errors.append(f"Parameter {i} missing 'type'")
                elif param["type"] not in ["string", "int", "bool"]:
                    errors.append(f"Parameter {i} has invalid type: {param['type']}")

    # Validate doc_refs if present
    if "doc_refs" in step:
        if not isinstance(step["doc_refs"], list):
            errors.append("'doc_refs' must be a list")
        else:
            for i, ref in enumerate(step["doc_refs"]):
                if not isinstance(ref, dict):
                    errors.append(f"doc_ref {i} must be a dict")
                    continue
                if "path" not in ref:
                    errors.append(f"doc_ref {i} missing 'path'")
                if "section" not in ref:
                    errors.append(f"doc_ref {i} missing 'section'")

    # Validate rag_assist if present
    if "rag_assist" in step:
        rag = step["rag_assist"]
        if not isinstance(rag, dict):
            errors.append("'rag_assist' must be a dict")
        else:
            if "query" not in rag:
                errors.append("rag_assist missing 'query'")

    # Validate validation if present
    if "validation" in step:
        val = step["validation"]
        if not isinstance(val, dict):
            errors.append("'validation' must be a dict")
        else:
            if "command" not in val:
                errors.append("validation missing 'command'")
            if "expect" not in val:
                errors.append("validation missing 'expect'")

    return len(errors) == 0, errors


def main() -> int:
    """Main validation function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Find workspace root
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    steps_dir = workspace_root / "steps"

    if not steps_dir.exists():
        print(f"❌ Steps directory not found: {steps_dir}")
        return 1

    # Find all step YAML files
    step_files = list(steps_dir.rglob("*.yaml"))
    if not step_files:
        print(f"⚠️  No step files found in {steps_dir}")
        return 0

    print(f"Validating {len(step_files)} step files...\n")

    # Validate each file
    all_valid = True
    for step_file in sorted(step_files):
        relative_path = step_file.relative_to(steps_dir)
        is_valid, errors = validate_step_file(step_file)

        if is_valid:
            print(f"✅ {relative_path}")
        else:
            print(f"❌ {relative_path}")
            for error in errors:
                print(f"   - {error}")
            all_valid = False

    # Summary
    print(f"\n{'='*60}")
    if all_valid:
        print(f"✅ All {len(step_files)} step files are valid!")
        return 0
    else:
        print(f"❌ Some step files have errors. Please fix them.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


"""Validate command - Run validation scripts."""

import subprocess
import sys
from pathlib import Path

import click


@click.command()
@click.option(
    "--runbooks",
    is_flag=True,
    help="Validate runbook YAML files",
)
@click.option(
    "--registry",
    is_flag=True,
    help="Validate runbook registry",
)
@click.option(
    "--steps",
    is_flag=True,
    help="Validate step library files",
)
@click.option(
    "--all",
    "validate_all",
    is_flag=True,
    help="Run all validations",
)
def validate(runbooks: bool, registry: bool, steps: bool, validate_all: bool) -> None:
    """Run validation scripts for runbooks, registry, and steps.

    This command runs the validation scripts to ensure:
    - Runbook YAML files are valid and reference existing docs
    - Registry entries match actual runbook files
    - Step library files have correct schema

    Examples:

        \b
        # Validate everything
        redis-agent-control-plane validate --all

        \b
        # Validate only runbooks
        redis-agent-control-plane validate --runbooks

        \b
        # Validate multiple components
        redis-agent-control-plane validate --runbooks --steps
    """
    # If no flags, default to --all
    if not any([runbooks, registry, steps, validate_all]):
        validate_all = True

    workspace_root = Path(__file__).parent.parent.parent.parent
    scripts_dir = workspace_root / "scripts"

    exit_code = 0

    if validate_all or runbooks:
        click.echo("=" * 80)
        click.echo("Validating runbooks...")
        click.echo("=" * 80)
        result = _run_script(scripts_dir / "validate_runbooks.py")
        if result != 0:
            exit_code = 1
        click.echo("")

    if validate_all or registry:
        click.echo("=" * 80)
        click.echo("Validating registry...")
        click.echo("=" * 80)
        result = _run_script(scripts_dir / "validate_registry.py")
        if result != 0:
            exit_code = 1
        click.echo("")

    if validate_all or steps:
        click.echo("=" * 80)
        click.echo("Validating steps...")
        click.echo("=" * 80)
        result = _run_script(scripts_dir / "validate_steps.py")
        if result != 0:
            exit_code = 1
        click.echo("")

    if exit_code == 0:
        click.echo("✅ All validations passed!")
    else:
        click.echo("❌ Some validations failed.", err=True)

    sys.exit(exit_code)


def _run_script(script_path: Path) -> int:
    """Run a validation script and return exit code."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent.parent,
            check=False,
            capture_output=False,
        )
        return result.returncode
    except Exception as e:
        click.echo(f"Error running {script_path.name}: {e}", err=True)
        return 1

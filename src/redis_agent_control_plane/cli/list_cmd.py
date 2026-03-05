"""List command - List available runbooks and steps."""

import sys
from pathlib import Path

import click
import yaml


@click.command()
@click.argument(
    "resource_type",
    type=click.Choice(["runbooks", "steps"]),
)
@click.option(
    "--filter",
    "-f",
    help="Filter by keyword (case-insensitive)",
)
def list_cmd(resource_type: str, filter: str | None) -> None:
    """List available runbooks or steps.

    This command shows all available runbooks or steps in the library.

    Examples:

        \b
        # List all runbooks
        redis-agent-control-plane list runbooks

        \b
        # List all steps
        redis-agent-control-plane list steps

        \b
        # Filter runbooks by keyword
        redis-agent-control-plane list runbooks --filter kubernetes
    """
    try:
        workspace_root = Path(__file__).parent.parent.parent.parent

        if resource_type == "runbooks":
            _list_runbooks(workspace_root, filter)
        elif resource_type == "steps":
            _list_steps(workspace_root, filter)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _list_runbooks(workspace_root: Path, filter_keyword: str | None) -> None:
    """List all runbooks."""
    runbooks_dir = workspace_root / "runbooks"
    runbook_files = sorted(runbooks_dir.rglob("*.yaml"))

    # Filter out _registry.yaml
    runbook_files = [f for f in runbook_files if f.name != "_registry.yaml"]

    if filter_keyword:
        filter_lower = filter_keyword.lower()
        runbook_files = [f for f in runbook_files if filter_lower in str(f).lower()]

    click.echo(f"Found {len(runbook_files)} runbooks:")
    click.echo("=" * 80)
    click.echo("")

    for runbook_file in runbook_files:
        # Load runbook to get metadata
        try:
            with open(runbook_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "runbook" in data:
                runbook_data = data["runbook"]
                runbook_id = runbook_data.get("id", "unknown")
                name = runbook_data.get("name", "Unknown")
                description = runbook_data.get("description", "")

                relative_path = runbook_file.relative_to(runbooks_dir)
                click.echo(f"📘 {runbook_id}")
                click.echo(f"   Name: {name}")
                click.echo(f"   Path: runbooks/{relative_path}")
                if description:
                    if len(description) > 100:
                        desc_preview = description[:100] + "..."
                    else:
                        desc_preview = description
                    click.echo(f"   Description: {desc_preview}")
                click.echo("")
        except Exception as e:
            click.echo(f"⚠️  Error loading {runbook_file.name}: {e}", err=True)
            click.echo("")


def _list_steps(workspace_root: Path, filter_keyword: str | None) -> None:
    """List all steps."""
    steps_dir = workspace_root / "steps"

    if not steps_dir.exists():
        click.echo("Steps directory not found.", err=True)
        return

    step_files = sorted(steps_dir.rglob("*.yaml"))

    # Filter out README
    step_files = [f for f in step_files if f.name != "README.md"]

    if filter_keyword:
        filter_lower = filter_keyword.lower()
        step_files = [f for f in step_files if filter_lower in str(f).lower()]

    click.echo(f"Found {len(step_files)} steps:")
    click.echo("=" * 80)
    click.echo("")

    for step_file in step_files:
        # Load step to get metadata
        try:
            with open(step_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data and "step" in data:
                step_data = data["step"]
                step_id = step_data.get("id", "unknown")
                name = step_data.get("name", "Unknown")
                description = step_data.get("description", "")

                relative_path = step_file.relative_to(steps_dir)
                # Remove .yaml extension for step_ref
                step_ref = str(relative_path).replace(".yaml", "")

                click.echo(f"🔧 {step_ref}")
                click.echo(f"   ID: {step_id}")
                click.echo(f"   Name: {name}")
                if description:
                    if len(description) > 100:
                        desc_preview = description[:100] + "..."
                    else:
                        desc_preview = description
                    click.echo(f"   Description: {desc_preview}")
                click.echo("")
        except Exception as e:
            click.echo(f"⚠️  Error loading {step_file.name}: {e}", err=True)
            click.echo("")
